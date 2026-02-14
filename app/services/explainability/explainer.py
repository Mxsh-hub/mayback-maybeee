from __future__ import annotations

from typing import Any


def build_explainability_payload(score_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "principles": [
            "Deterministic scoring only",
            "AI used only for semantic labels",
            "All dimensions expose intermediate metrics and formulas",
            "No black-box ML scoring",
        ],
        "dimension_formulas": {
            "cash_flow_health": "0.40*IncomeExpense + 0.35*NetSavings + 0.25*CashflowStability",
            "spending_discipline": "100*(0.40*PlannedRatio + 0.30*(1-ImpulseRatio) + 0.30*(1-SpikeFrequency))",
            "commitment_reliability": "100*(0.45*OnTime + 0.35*Consistency + 0.20*(1-MissedRatio))",
            "financial_resilience": "0.25*EmergencyBuffer + 0.25*ShockFrequency + 0.30*Recovery + 0.20*Volatility",
        },
        "normalization": score_result.get("meta", {}),
    }
