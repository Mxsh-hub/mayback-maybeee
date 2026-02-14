from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.db_models import Transaction
from app.services.ai_classifier.ollama_client import OllamaClient
from app.services.ai_classifier.prompting import (
    CLASSIFICATION_JSON_SCHEMA,
    build_classification_prompt,
)
from app.services.ai_classifier.repository import (
    bulk_upsert_classifications,
    fetch_classifications_by_transaction_ids,
)

ALLOWED_CATEGORY = {"essential", "non_essential", "emergency"}
ALLOWED_INTENT = {"planned", "impulse", "na"}


class AIClassificationError(Exception):
    """Raised when classification fails strict validation."""


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    intent_label: str
    essentiality: int


def _validate_strict_payload(payload: dict) -> ClassificationResult:
    required_keys = {"category", "intent_label", "essentiality"}
    if set(payload.keys()) != required_keys:
        raise AIClassificationError("AI output must contain exactly category, intent_label, essentiality")

    category = payload.get("category")
    intent_label = payload.get("intent_label")
    essentiality = payload.get("essentiality")

    if category not in ALLOWED_CATEGORY:
        raise AIClassificationError(f"Invalid category: {category}")

    if intent_label not in ALLOWED_INTENT:
        raise AIClassificationError(f"Invalid intent_label: {intent_label}")

    if category == "non_essential" and intent_label not in {"planned", "impulse"}:
        raise AIClassificationError("Non-essential transactions require planned or impulse intent")

    if category in {"essential", "emergency"} and intent_label != "na":
        raise AIClassificationError("Essential or emergency transactions must use intent_label='na'")

    if isinstance(essentiality, bool) or not isinstance(essentiality, int):
        raise AIClassificationError("Essentiality must be an integer")

    if essentiality < 0 or essentiality > 10:
        raise AIClassificationError("Essentiality must be within 0-10")

    return ClassificationResult(
        category=category,
        intent_label=intent_label,
        essentiality=essentiality,
    )


def _extract_required_payload(payload: dict) -> dict:
    required = {"category", "intent_label", "essentiality"}

    candidates: list[dict] = [payload]
    for value in payload.values():
        if isinstance(value, dict):
            candidates.append(value)

    for candidate in candidates:
        if required.issubset(candidate.keys()):
            normalized = {
                "category": candidate["category"],
                "intent_label": candidate["intent_label"],
                "essentiality": candidate["essentiality"],
            }

            if isinstance(normalized["category"], str):
                normalized["category"] = normalized["category"].strip().lower()
            if isinstance(normalized["intent_label"], str):
                normalized["intent_label"] = normalized["intent_label"].strip().lower()

            essentiality = normalized["essentiality"]
            if isinstance(essentiality, str):
                stripped = essentiality.strip()
                if stripped.isdigit():
                    normalized["essentiality"] = int(stripped)
            elif isinstance(essentiality, float) and essentiality.is_integer():
                normalized["essentiality"] = int(essentiality)

            return normalized

    raise AIClassificationError("AI output missing required keys: category, intent_label, essentiality")


class AIClassifierService:
    def __init__(self, client: OllamaClient | None = None) -> None:
        settings = get_settings()
        self.client = client or OllamaClient()
        self.model_name = settings.ollama_model
        self.max_retries = max(1, settings.ai_max_retries)

    def _classify_transaction(self, txn: Transaction) -> ClassificationResult:
        prompt = build_classification_prompt(
            txn_date=txn.txn_date,
            description=txn.description,
            amount=float(txn.amount),
        )

        last_exc: Exception | None = None
        for _ in range(self.max_retries):
            try:
                payload = self.client.generate_json(
                    prompt=prompt,
                    schema=CLASSIFICATION_JSON_SCHEMA,
                )
                normalized = _extract_required_payload(payload)
                return _validate_strict_payload(normalized)
            except Exception as exc:  # noqa: BLE001
                last_exc = exc

        raise AIClassificationError(f"Classification failed after retries: {last_exc}")

    def ensure_expense_classifications(self, db: Session, expenses: list[Transaction]) -> dict[str, int]:
        if not expenses:
            return {"scanned_expenses": 0, "newly_classified": 0, "already_cached": 0}

        tx_ids = [tx.id for tx in expenses]
        cached = fetch_classifications_by_transaction_ids(db, tx_ids)

        missing = [tx for tx in expenses if tx.id not in cached]
        if not missing:
            return {
                "scanned_expenses": len(expenses),
                "newly_classified": 0,
                "already_cached": len(cached),
            }

        rows: list[dict] = []
        for tx in missing:
            result = self._classify_transaction(tx)
            rows.append(
                {
                    "transaction_id": tx.id,
                    "category": result.category,
                    "intent_label": result.intent_label,
                    "essentiality": result.essentiality,
                    "model_name": self.model_name,
                    "raw_json": json.dumps(
                        {
                            "category": result.category,
                            "intent_label": result.intent_label,
                            "essentiality": result.essentiality,
                        },
                        ensure_ascii=True,
                    ),
                }
            )

        bulk_upsert_classifications(db, rows)
        return {
            "scanned_expenses": len(expenses),
            "newly_classified": len(rows),
            "already_cached": len(cached),
        }
