from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.services.scoring.config import ScoringConfig, load_scoring_config

COMMITMENT_PATTERN = re.compile(
    r"(emi|rent|credit\s*card|loan|mortgage|insurance|tuition|utility)",
    re.IGNORECASE,
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _linear_scale(value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 100.0
    return ((value - low) / (high - low)) * 100.0


def _inverse_linear_scale(value: float, low: float, high: float) -> float:
    if value <= low:
        return 100.0
    if value >= high:
        return 0.0
    return (1.0 - ((value - low) / (high - low))) * 100.0


def _period_distance_in_months(start: pd.Period, end: pd.Period) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


def _normalize_input_frame(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    if df.empty:
        return df

    df["txn_date"] = pd.to_datetime(df["txn_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["description"] = df["description"].fillna("").astype(str)
    df["category"] = df["category"].fillna("unclassified")
    df["intent_label"] = df["intent_label"].fillna("na")

    # Essentiality is deterministic downstream, so unknown values are forced to 0.
    df["essentiality"] = pd.to_numeric(df["essentiality"], errors="coerce").fillna(0).astype(int)
    df["essentiality"] = df["essentiality"].clip(lower=0, upper=10)
    df["month"] = df["txn_date"].dt.to_period("M")
    return df


def _cash_flow_health(df: pd.DataFrame) -> tuple[float, dict[str, Any]]:
    income_df = df[df["direction"] == "income"]
    expense_df = df[df["direction"] == "expense"]

    total_income = float(income_df["amount"].sum())
    total_expense = float(expense_df["amount"].sum())

    income_expense_ratio = _safe_div(total_income, total_expense)
    income_expense_score = _linear_scale(income_expense_ratio, low=1.0, high=2.0)

    net_savings_rate = _safe_div(total_income - total_expense, total_income) if total_income > 0 else -1.0
    net_savings_score = _linear_scale(net_savings_rate, low=0.0, high=0.4)

    if expense_df.empty:
        avg_essentiality = 0.0
        weighted_essential_ratio = 0.0
    else:
        avg_essentiality = float(expense_df["essentiality"].mean())
        weighted_essential_ratio = _safe_div(
            float((expense_df["amount"] * (expense_df["essentiality"] / 10.0)).sum()),
            total_expense,
        )

    stability_raw = _clamp((0.6 * avg_essentiality) + (4.0 * weighted_essential_ratio), 0.0, 10.0)
    stability_score = stability_raw * 10.0

    score = (0.40 * income_expense_score) + (0.35 * net_savings_score) + (0.25 * stability_score)

    details = {
        "income_expense_ratio": round(income_expense_ratio, 4),
        "income_expense_score": round(income_expense_score, 2),
        "net_savings_rate": round(net_savings_rate, 4),
        "net_savings_score": round(net_savings_score, 2),
        "avg_essentiality": round(avg_essentiality, 2),
        "weighted_essential_spending_ratio": round(weighted_essential_ratio, 4),
        "cashflow_stability_raw_0_10": round(stability_raw, 2),
        "cashflow_stability_score": round(stability_score, 2),
        "formula": "0.40*income_expense + 0.35*net_savings + 0.25*cashflow_stability",
    }
    return _clamp(score, 0.0, 100.0), details


def _spending_discipline(df: pd.DataFrame, config: ScoringConfig) -> tuple[float, dict[str, Any]]:
    income_df = df[df["direction"] == "income"]
    expense_df = df[df["direction"] == "expense"]

    monthly_income = income_df.groupby("month")["amount"].sum().to_dict()
    non_essential = expense_df[expense_df["category"] == "non_essential"].copy()

    if non_essential.empty:
        return 100.0, {
            "non_essential_tx_count": 0,
            "planned_ratio": 1.0,
            "impulse_ratio": 0.0,
            "spike_frequency": 0.0,
            "formula": "No non-essential spending => full discipline",
        }

    non_essential = non_essential.sort_values("txn_date")
    baseline_global = float(non_essential["amount"].median()) if not non_essential.empty else 0.0

    total_non_essential = len(non_essential)
    total_spikes = 0
    monthly_spike_rates: list[float] = []

    for month in sorted(non_essential["month"].dropna().unique()):
        current = non_essential[non_essential["month"] == month]
        history = non_essential[non_essential["month"] < month]

        baseline = float(history["amount"].median()) if not history.empty else baseline_global
        if baseline <= 0:
            baseline = float(current["amount"].median())

        income_for_month = float(monthly_income.get(month, 0.0))

        month_spikes = 0
        for amount in current["amount"].tolist():
            by_income = (
                income_for_month > 0
                and amount > (config.thresholds.impulse_income_pct * income_for_month)
            )
            by_baseline = (
                baseline > 0
                and amount > (config.thresholds.discretionary_deviation_multiplier * baseline)
            )
            if by_income or by_baseline:
                month_spikes += 1

        total_spikes += month_spikes
        monthly_spike_rates.append(month_spikes / max(len(current), 1))

    planned_count = int((non_essential["intent_label"] == "planned").sum())
    impulse_count = int((non_essential["intent_label"] == "impulse").sum())

    planned_ratio = planned_count / total_non_essential
    impulse_ratio = impulse_count / total_non_essential
    spike_frequency = (
        sum(monthly_spike_rates) / len(monthly_spike_rates) if monthly_spike_rates else 0.0
    )

    score = 100.0 * (
        (0.40 * planned_ratio)
        + (0.30 * (1.0 - impulse_ratio))
        + (0.30 * (1.0 - spike_frequency))
    )

    details = {
        "non_essential_tx_count": total_non_essential,
        "planned_ratio": round(planned_ratio, 4),
        "impulse_ratio": round(impulse_ratio, 4),
        "spike_count": total_spikes,
        "spike_frequency": round(spike_frequency, 4),
        "impulse_income_pct_threshold": config.thresholds.impulse_income_pct,
        "deviation_multiplier": config.thresholds.discretionary_deviation_multiplier,
        "formula": "100*(0.40*planned_ratio + 0.30*(1-impulse_ratio) + 0.30*(1-spike_frequency))",
    }
    return _clamp(score, 0.0, 100.0), details


def _commitment_reliability(df: pd.DataFrame, config: ScoringConfig) -> tuple[float, dict[str, Any]]:
    expense_df = df[df["direction"] == "expense"].copy()
    commitment_df = expense_df[
        expense_df["description"].str.contains(COMMITMENT_PATTERN, regex=True, na=False)
    ].copy()

    if commitment_df.empty:
        return 100.0, {
            "commitment_series": 0,
            "expected_payments": 0,
            "observed_payments": 0,
            "on_time_payments": 0,
            "missed_payments": 0,
            "formula": "No commitments detected => full reliability",
        }

    commitment_df["commitment_key"] = (
        commitment_df["description"]
        .str.extract(COMMITMENT_PATTERN, expand=False)
        .fillna("other")
        .str.lower()
    )

    total_expected = 0
    total_observed = 0
    total_on_time = 0
    total_missed = 0

    for _, group in commitment_df.groupby("commitment_key"):
        monthly_days = group.groupby("month")["txn_date"].apply(lambda s: int(round(s.dt.day.median())))
        if monthly_days.empty:
            continue

        observed = len(monthly_days)
        min_month = monthly_days.index.min()
        max_month = monthly_days.index.max()

        expected = (
            _period_distance_in_months(start=min_month, end=max_month) + 1
            if observed >= 2
            else 1
        )

        due_day = int(round(float(monthly_days.median())))
        on_time = int((monthly_days.apply(lambda day: abs(day - due_day) <= config.thresholds.commitment_on_time_grace_days)).sum())

        missed = max(expected - observed, 0)

        total_expected += expected
        total_observed += observed
        total_on_time += on_time
        total_missed += missed

    if total_expected == 0:
        return 100.0, {
            "commitment_series": 0,
            "expected_payments": 0,
            "observed_payments": 0,
            "on_time_payments": 0,
            "missed_payments": 0,
            "formula": "No commitments detected => full reliability",
        }

    consistency_ratio = _safe_div(total_observed, total_expected)
    on_time_ratio = _safe_div(total_on_time, total_observed)
    missed_ratio = _safe_div(total_missed, total_expected)

    score = 100.0 * (
        (0.45 * on_time_ratio)
        + (0.35 * consistency_ratio)
        + (0.20 * (1.0 - missed_ratio))
    )

    details = {
        "expected_payments": total_expected,
        "observed_payments": total_observed,
        "on_time_payments": total_on_time,
        "missed_payments": total_missed,
        "consistency_ratio": round(consistency_ratio, 4),
        "on_time_ratio": round(on_time_ratio, 4),
        "missed_ratio": round(missed_ratio, 4),
        "grace_days": config.thresholds.commitment_on_time_grace_days,
        "formula": "100*(0.45*on_time + 0.35*consistency + 0.20*(1-missed_ratio))",
    }
    return _clamp(score, 0.0, 100.0), details


def _financial_resilience(df: pd.DataFrame, config: ScoringConfig) -> tuple[float, dict[str, Any]]:
    income_df = df[df["direction"] == "income"]
    expense_df = df[df["direction"] == "expense"]
    emergency_df = expense_df[expense_df["category"] == "emergency"].copy()

    monthly_income = income_df.groupby("month")["amount"].sum().sort_index()
    monthly_expense = expense_df.groupby("month")["amount"].sum().sort_index()
    monthly_net = monthly_income.sub(monthly_expense, fill_value=0.0).sort_index()

    month_index = list(monthly_net.index)
    monthly_emergency = emergency_df.groupby("month")["amount"].sum().to_dict()

    shock_months: list[pd.Period] = []
    for month in month_index:
        emergency_amt = float(monthly_emergency.get(month, 0.0))
        income_amt = float(monthly_income.get(month, 0.0))

        if emergency_amt <= 0:
            continue

        is_shock = (
            income_amt <= 0
            or emergency_amt > (config.thresholds.emergency_shock_income_pct * income_amt)
        )
        if is_shock:
            shock_months.append(month)

    recovery_windows: list[int] = []
    for shock_month in shock_months:
        shock_pos = month_index.index(shock_month)
        recovery = config.thresholds.recovery_cap_months

        for idx in range(shock_pos + 1, len(month_index)):
            if float(monthly_net.iloc[idx]) >= 0:
                recovery = idx - shock_pos
                break

        recovery_windows.append(recovery)

    avg_recovery_months = (
        float(sum(recovery_windows) / len(recovery_windows)) if recovery_windows else 0.0
    )

    total_income = float(income_df["amount"].sum())
    total_emergency = float(emergency_df["amount"].sum()) if not emergency_df.empty else 0.0

    if total_income > 0:
        emergency_ratio = _safe_div(total_emergency, total_income)
    else:
        emergency_ratio = 1.0 if total_emergency > 0 else 0.0
    emergency_buffer_score = _inverse_linear_scale(emergency_ratio, low=0.0, high=0.30)

    months_count = max(len(month_index), 1)
    shock_frequency = len(shock_months) / months_count
    shock_frequency_score = _inverse_linear_scale(shock_frequency, low=0.0, high=1.0)

    recovery_score = _inverse_linear_scale(
        avg_recovery_months,
        low=0.0,
        high=float(config.thresholds.recovery_cap_months),
    )

    volatility_ratio = 0.0
    if len(monthly_net) > 0:
        mean_monthly_income = float(monthly_income.mean()) if len(monthly_income) > 0 else 0.0
        volatility_ratio = _safe_div(float(monthly_net.std(ddof=0)), max(mean_monthly_income, 1e-9))

    volatility_score = _inverse_linear_scale(volatility_ratio, low=0.0, high=1.0)

    score = (
        (0.25 * emergency_buffer_score)
        + (0.25 * shock_frequency_score)
        + (0.30 * recovery_score)
        + (0.20 * volatility_score)
    )

    details = {
        "emergency_spend_ratio": round(emergency_ratio, 4),
        "emergency_events": int(len(emergency_df)),
        "shock_months": [str(m) for m in shock_months],
        "shock_frequency": round(shock_frequency, 4),
        "avg_recovery_months": round(avg_recovery_months, 2),
        "volatility_ratio": round(volatility_ratio, 4),
        "formula": "0.25*buffer + 0.25*shock_frequency + 0.30*recovery + 0.20*volatility",
    }
    return _clamp(score, 0.0, 100.0), details


def compute_trust_index(frame: pd.DataFrame, config: ScoringConfig | None = None) -> dict[str, Any]:
    cfg = config or load_scoring_config()
    df = _normalize_input_frame(frame)

    if df.empty:
        return {
            "trust_index": 0.0,
            "dimensions": {
                "cash_flow_health": {"score": 0.0, "weight": cfg.weights.cash_flow_health, "weighted_contribution": 0.0, "details": {}},
                "spending_discipline": {"score": 0.0, "weight": cfg.weights.spending_discipline, "weighted_contribution": 0.0, "details": {}},
                "commitment_reliability": {"score": 0.0, "weight": cfg.weights.commitment_reliability, "weighted_contribution": 0.0, "details": {}},
                "financial_resilience": {"score": 0.0, "weight": cfg.weights.financial_resilience, "weighted_contribution": 0.0, "details": {}},
            },
            "meta": {"weight_sum": 90.0, "normalized": True},
        }

    cash_score, cash_details = _cash_flow_health(df)
    discipline_score, discipline_details = _spending_discipline(df, cfg)
    commitment_score, commitment_details = _commitment_reliability(df, cfg)
    resilience_score, resilience_details = _financial_resilience(df, cfg)

    weights = {
        "cash_flow_health": cfg.weights.cash_flow_health,
        "spending_discipline": cfg.weights.spending_discipline,
        "commitment_reliability": cfg.weights.commitment_reliability,
        "financial_resilience": cfg.weights.financial_resilience,
    }

    raw_scores = {
        "cash_flow_health": cash_score,
        "spending_discipline": discipline_score,
        "commitment_reliability": commitment_score,
        "financial_resilience": resilience_score,
    }

    raw_details = {
        "cash_flow_health": cash_details,
        "spending_discipline": discipline_details,
        "commitment_reliability": commitment_details,
        "financial_resilience": resilience_details,
    }

    weight_sum = sum(weights.values())
    dimensions: dict[str, dict[str, Any]] = {}
    trust_index = 0.0

    for dim_name, score in raw_scores.items():
        contribution = (score * weights[dim_name]) / weight_sum
        trust_index += contribution
        dimensions[dim_name] = {
            "score": round(_clamp(score, 0.0, 100.0), 2),
            "weight": round(weights[dim_name], 2),
            "weighted_contribution": round(contribution, 2),
            "details": raw_details[dim_name],
        }

    return {
        "trust_index": round(_clamp(trust_index, 0.0, 100.0), 2),
        "dimensions": dimensions,
        "meta": {
            "weight_sum": weight_sum,
            "normalized": True,
            "normalization_note": "Dimension weights sum to 90; scores are normalized to a 0-100 Trust Index.",
        },
    }
