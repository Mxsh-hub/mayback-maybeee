from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from sqlalchemy.orm import Session

from app.models.db_models import Transaction
from app.models.schemas import TransactionIn
from app.services.data_loader.repository import bulk_upsert_transactions


def ingest_transactions(db: Session, transactions: Sequence[TransactionIn]) -> dict[str, int]:
    inserted, updated = bulk_upsert_transactions(db=db, transactions=list(transactions))
    return {
        "received": len(transactions),
        "inserted": inserted,
        "updated": updated,
    }


def transactions_to_dataframe(transactions: Sequence[Transaction]) -> pd.DataFrame:
    rows: list[dict] = []

    for txn in transactions:
        cls = txn.classification
        rows.append(
            {
                "transaction_id": txn.id,
                "user_id": txn.user_id,
                "transaction_ref": txn.transaction_ref,
                "txn_date": txn.txn_date,
                "description": txn.description,
                "amount": float(txn.amount),
                "direction": txn.direction,
                "source": txn.source,
                "category": cls.category if cls else None,
                "intent_label": cls.intent_label if cls else None,
                "essentiality": int(cls.essentiality) if cls else None,
            }
        )

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["txn_date"] = pd.to_datetime(frame["txn_date"], utc=False)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0)
    return frame
