from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


def _chunked(items: Sequence[dict[str, Any]], chunk_size: int) -> Iterable[Sequence[dict[str, Any]]]:
    for idx in range(0, len(items), chunk_size):
        yield items[idx : idx + chunk_size]


def _load_urls() -> tuple[str, str]:
    load_dotenv()

    source_mysql_url = os.getenv("SOURCE_MYSQL_URL") or os.getenv("MYSQL_URL")
    target_database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")

    if not source_mysql_url:
        raise RuntimeError("Missing SOURCE_MYSQL_URL (or MYSQL_URL) in environment.")
    if not target_database_url:
        raise RuntimeError("Missing DATABASE_URL (or SUPABASE_DB_URL) in environment.")

    if "pymysql" not in source_mysql_url:
        raise RuntimeError("SOURCE_MYSQL_URL must be a MySQL connection string using pymysql.")
    if "postgresql" not in target_database_url:
        raise RuntimeError("DATABASE_URL must be a PostgreSQL connection string (Supabase).")

    return source_mysql_url, target_database_url


def _fetch_source_rows(source_mysql_url: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_engine = create_engine(source_mysql_url, pool_pre_ping=True, future=True)
    with source_engine.connect() as conn:
        tx_rows = conn.execute(
            text(
                """
                SELECT
                    id,
                    user_id,
                    transaction_ref,
                    txn_date,
                    description,
                    amount,
                    direction,
                    source,
                    created_at,
                    updated_at
                FROM transactions
                ORDER BY id
                """
            )
        ).mappings()
        class_rows = conn.execute(
            text(
                """
                SELECT
                    id,
                    transaction_id,
                    category,
                    intent_label,
                    essentiality,
                    model_name,
                    raw_json,
                    created_at,
                    updated_at
                FROM transaction_classifications
                ORDER BY id
                """
            )
        ).mappings()
        transactions = [dict(row) for row in tx_rows]
        classifications = [dict(row) for row in class_rows]

    source_engine.dispose()
    return transactions, classifications


def _assert_target_schema(session: Session) -> None:
    required = {"transactions", "transaction_classifications"}
    rows = session.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('transactions', 'transaction_classifications')
            """
        )
    ).all()
    existing = {row[0] for row in rows}
    missing = required - existing
    if missing:
        names = ", ".join(sorted(missing))
        raise RuntimeError(
            f"Missing target tables: {names}. Start the FastAPI app against Supabase once to auto-create schema, then rerun migration."
        )


def _upsert_transactions(session: Session, transactions: list[dict[str, Any]]) -> None:
    if not transactions:
        return

    stmt = text(
        """
        INSERT INTO transactions (
            id,
            user_id,
            transaction_ref,
            txn_date,
            description,
            amount,
            direction,
            source,
            created_at,
            updated_at
        ) VALUES (
            :id,
            :user_id,
            :transaction_ref,
            :txn_date,
            :description,
            :amount,
            :direction,
            :source,
            :created_at,
            :updated_at
        )
        ON CONFLICT (id) DO UPDATE SET
            user_id = EXCLUDED.user_id,
            transaction_ref = EXCLUDED.transaction_ref,
            txn_date = EXCLUDED.txn_date,
            description = EXCLUDED.description,
            amount = EXCLUDED.amount,
            direction = EXCLUDED.direction,
            source = EXCLUDED.source,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at
        """
    )

    for chunk in _chunked(transactions, 1000):
        session.execute(stmt, list(chunk))


def _upsert_classifications(session: Session, classifications: list[dict[str, Any]]) -> None:
    if not classifications:
        return

    stmt = text(
        """
        INSERT INTO transaction_classifications (
            id,
            transaction_id,
            category,
            intent_label,
            essentiality,
            model_name,
            raw_json,
            created_at,
            updated_at
        ) VALUES (
            :id,
            :transaction_id,
            :category,
            :intent_label,
            :essentiality,
            :model_name,
            :raw_json,
            :created_at,
            :updated_at
        )
        ON CONFLICT (id) DO UPDATE SET
            transaction_id = EXCLUDED.transaction_id,
            category = EXCLUDED.category,
            intent_label = EXCLUDED.intent_label,
            essentiality = EXCLUDED.essentiality,
            model_name = EXCLUDED.model_name,
            raw_json = EXCLUDED.raw_json,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at
        """
    )

    for chunk in _chunked(classifications, 1000):
        session.execute(stmt, list(chunk))


def _sync_sequences(session: Session) -> None:
    session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('transactions', 'id'),
                COALESCE((SELECT MAX(id) FROM transactions), 1),
                true
            )
            """
        )
    )
    session.execute(
        text(
            """
            SELECT setval(
                pg_get_serial_sequence('transaction_classifications', 'id'),
                COALESCE((SELECT MAX(id) FROM transaction_classifications), 1),
                true
            )
            """
        )
    )


def _count_rows(session: Session, table_name: str) -> int:
    return int(session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar_one())


def main() -> None:
    source_mysql_url, target_database_url = _load_urls()
    transactions, classifications = _fetch_source_rows(source_mysql_url)

    target_engine = create_engine(target_database_url, pool_pre_ping=True, future=True)
    with Session(target_engine) as session:
        _assert_target_schema(session)
        _upsert_transactions(session, transactions)
        _upsert_classifications(session, classifications)
        _sync_sequences(session)
        session.commit()

        target_transactions = _count_rows(session, "transactions")
        target_classifications = _count_rows(session, "transaction_classifications")

    target_engine.dispose()

    print(f"Source transactions: {len(transactions)}")
    print(f"Source classifications: {len(classifications)}")
    print(f"Target transactions: {target_transactions}")
    print(f"Target classifications: {target_classifications}")
    print("Migration complete.")


if __name__ == "__main__":
    main()
