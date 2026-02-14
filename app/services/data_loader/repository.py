from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from datetime import datetime

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session, selectinload

from app.models.db_models import Transaction
from app.models.schemas import TransactionIn


def _chunked(items: Sequence, chunk_size: int) -> Iterable[Sequence]:
    for idx in range(0, len(items), chunk_size):
        yield items[idx : idx + chunk_size]


def build_transaction_ref(txn: TransactionIn) -> str:
    if txn.transaction_ref:
        return txn.transaction_ref

    payload = "|".join(
        [
            txn.user_id,
            txn.txn_date.isoformat(),
            txn.description.strip().lower(),
            f"{txn.amount:.2f}",
            txn.direction,
            txn.source or "",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def bulk_upsert_transactions(db: Session, transactions: list[TransactionIn]) -> tuple[int, int]:
    if not transactions:
        return 0, 0

    deduped_rows: dict[tuple[str, str], dict] = {}
    now = datetime.utcnow()

    for txn in transactions:
        tx_ref = build_transaction_ref(txn)
        deduped_rows[(txn.user_id, tx_ref)] = {
            "user_id": txn.user_id,
            "transaction_ref": tx_ref,
            "txn_date": txn.txn_date,
            "description": txn.description,
            "amount": txn.amount,
            "direction": txn.direction,
            "source": txn.source,
            "created_at": now,
            "updated_at": now,
        }

    rows = list(deduped_rows.values())
    keys = list(deduped_rows.keys())

    existing_keys: set[tuple[str, str]] = set()
    for key_chunk in _chunked(keys, 500):
        stmt = select(Transaction.user_id, Transaction.transaction_ref).where(
            tuple_(Transaction.user_id, Transaction.transaction_ref).in_(key_chunk)
        )
        existing_keys.update((row[0], row[1]) for row in db.execute(stmt).all())

    for row_chunk in _chunked(rows, 1000):
        stmt = mysql_insert(Transaction).values(list(row_chunk))
        update_map = {
            "txn_date": stmt.inserted.txn_date,
            "description": stmt.inserted.description,
            "amount": stmt.inserted.amount,
            "direction": stmt.inserted.direction,
            "source": stmt.inserted.source,
            "updated_at": func.now(),
        }
        db.execute(stmt.on_duplicate_key_update(**update_map))

    db.commit()

    updated = len(existing_keys)
    inserted = len(rows) - updated
    return inserted, updated


def fetch_transactions_with_classification(
    db: Session,
    user_id: str,
    start_date=None,
    end_date=None,
) -> list[Transaction]:
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.classification))
        .where(Transaction.user_id == user_id)
    )

    if start_date is not None:
        stmt = stmt.where(Transaction.txn_date >= start_date)
    if end_date is not None:
        stmt = stmt.where(Transaction.txn_date <= end_date)

    stmt = stmt.order_by(Transaction.txn_date.asc(), Transaction.id.asc())
    return list(db.scalars(stmt).all())


def delete_seed_transactions_by_user(
    db: Session,
    user_id: str,
    source: str = "seed_dataset_v1",
) -> int:
    stmt = delete(Transaction).where(
        Transaction.user_id == user_id,
        Transaction.source == source,
    )
    result = db.execute(stmt)
    db.commit()
    return int(result.rowcount or 0)
