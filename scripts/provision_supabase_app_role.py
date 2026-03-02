from __future__ import annotations

import os
import re
import secrets
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def _validate_identifier(name: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"Invalid {label}: {name}. Allowed pattern: [A-Za-z_][A-Za-z0-9_]*")
    return name


def _database_name_from_url(db_url: str) -> str:
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip("/") or "postgres"
    return _validate_identifier(db_name, "database name")


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> None:
    load_dotenv()

    admin_db_url = os.getenv("ADMIN_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not admin_db_url:
        raise RuntimeError("Missing ADMIN_DATABASE_URL (or DATABASE_URL) in environment.")

    app_role = _validate_identifier(os.getenv("APP_DB_ROLE", "trust_index_app"), "app role")
    app_password = os.getenv("APP_DB_PASSWORD") or secrets.token_urlsafe(24)
    project_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip()
    db_name = _database_name_from_url(admin_db_url)

    role_sql_name = f'"{app_role}"'
    tx_policy = _validate_identifier(f"transactions_{app_role}_all", "transaction policy name")
    cls_policy = _validate_identifier(f"classifications_{app_role}_all", "classification policy name")

    app_password_literal = _sql_literal(app_password)

    sql_statements = [
        f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{app_role}') THEN CREATE ROLE {role_sql_name} LOGIN PASSWORD {app_password_literal} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT; ELSE ALTER ROLE {role_sql_name} WITH LOGIN PASSWORD {app_password_literal} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT; END IF; END $$;",
        f"GRANT CONNECT ON DATABASE {db_name} TO {role_sql_name};",
        f"GRANT USAGE ON SCHEMA public TO {role_sql_name};",
        f"REVOKE CREATE ON SCHEMA public FROM {role_sql_name};",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.transactions TO {role_sql_name};",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.transaction_classifications TO {role_sql_name};",
        f"GRANT USAGE, SELECT ON SEQUENCE public.transactions_id_seq TO {role_sql_name};",
        f"GRANT USAGE, SELECT ON SEQUENCE public.transaction_classifications_id_seq TO {role_sql_name};",
        "ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.transactions FORCE ROW LEVEL SECURITY;",
        "ALTER TABLE public.transaction_classifications ENABLE ROW LEVEL SECURITY;",
        "ALTER TABLE public.transaction_classifications FORCE ROW LEVEL SECURITY;",
        f"DROP POLICY IF EXISTS {tx_policy} ON public.transactions;",
        f"CREATE POLICY {tx_policy} ON public.transactions FOR ALL TO {role_sql_name} USING (true) WITH CHECK (true);",
        f"DROP POLICY IF EXISTS {cls_policy} ON public.transaction_classifications;",
        f"CREATE POLICY {cls_policy} ON public.transaction_classifications FOR ALL TO {role_sql_name} USING (true) WITH CHECK (true);",
    ]

    engine = create_engine(admin_db_url, future=True)
    with engine.begin() as conn:
        for statement in sql_statements:
            conn.execute(text(statement))

        rls_rows = conn.execute(
            text(
                """
                SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled, c.relforcerowsecurity AS rls_forced
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relname IN ('transactions', 'transaction_classifications')
                ORDER BY c.relname
                """
            )
        ).all()

    engine.dispose()

    pooler_username = f"{app_role}.{project_ref}" if project_ref else f"{app_role}.<PROJECT_REF>"
    print("Provisioning complete.")
    print(f"Role: {app_role}")
    print(f"Password: {app_password}")
    print("RLS status:")
    for row in rls_rows:
        print(f"- {row.table_name}: enabled={row.rls_enabled}, forced={row.rls_forced}")
    print("Use this runtime DATABASE_URL for Supabase pooler:")
    print(f"postgresql+psycopg://{pooler_username}:{app_password}@aws-1-ap-northeast-2.pooler.supabase.com:5432/{db_name}?sslmode=require")


if __name__ == "__main__":
    main()
