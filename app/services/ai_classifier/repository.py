from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.db_models import TransactionClassification


def _chunked(items: Sequence, chunk_size: int) -> Iterable[Sequence]:
    for idx in range(0, len(items), chunk_size):
        yield items[idx : idx + chunk_size]


def fetch_classifications_by_transaction_ids(
    db: Session,
    transaction_ids: list[int],
) -> dict[int, TransactionClassification]:
    if not transaction_ids:
        return {}

    result: dict[int, TransactionClassification] = {}
    for tx_chunk in _chunked(transaction_ids, 1000):
        stmt = select(TransactionClassification).where(TransactionClassification.transaction_id.in_(tx_chunk))
        for row in db.scalars(stmt).all():
            result[row.transaction_id] = row

    return result


def bulk_upsert_classifications(db: Session, records: list[dict]) -> None:
    if not records:
        return

    now = datetime.utcnow()
    deduped: dict[int, dict] = {}
    for row in records:
        deduped[row["transaction_id"]] = {**row, "created_at": now, "updated_at": now}
    rows = list(deduped.values())

    for row_chunk in _chunked(rows, 500):
        stmt = pg_insert(TransactionClassification).values(list(row_chunk))
        update_map = {
            "category": stmt.excluded.category,
            "intent_label": stmt.excluded.intent_label,
            "essentiality": stmt.excluded.essentiality,
            "model_name": stmt.excluded.model_name,
            "raw_json": stmt.excluded.raw_json,
            "updated_at": stmt.excluded.updated_at,
        }
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=[TransactionClassification.transaction_id],
                set_=update_map,
            )
        )

    db.commit()
