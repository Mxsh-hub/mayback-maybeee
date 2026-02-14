from dataclasses import dataclass

from app.config import get_settings


@dataclass(frozen=True)
class DimensionWeights:
    cash_flow_health: float = 30.0
    spending_discipline: float = 20.0
    commitment_reliability: float = 25.0
    financial_resilience: float = 15.0


@dataclass(frozen=True)
class Thresholds:
    impulse_income_pct: float
    discretionary_deviation_multiplier: float
    commitment_on_time_grace_days: int
    emergency_shock_income_pct: float
    recovery_cap_months: int


@dataclass(frozen=True)
class ScoringConfig:
    weights: DimensionWeights
    thresholds: Thresholds


def load_scoring_config() -> ScoringConfig:
    settings = get_settings()
    return ScoringConfig(
        weights=DimensionWeights(),
        thresholds=Thresholds(
            impulse_income_pct=settings.impulse_income_pct,
            discretionary_deviation_multiplier=settings.discretionary_deviation_multiplier,
            commitment_on_time_grace_days=settings.commitment_on_time_grace_days,
            emergency_shock_income_pct=settings.emergency_shock_income_pct,
            recovery_cap_months=settings.recovery_cap_months,
        ),
    )
