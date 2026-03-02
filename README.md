# Multi-Dimensional Trust Index (FastAPI + Supabase Postgres + Ollama)

Deterministic behavioral financial scoring with explainable 0-100 output.

## What this prototype enforces

- AI is semantic-only (category, intent, essentiality).
- AI never computes score values.
- Scoring is deterministic and formula-driven.
- All dimension details are exposed for judge-friendly explainability.
- Classification outputs are cached in Supabase Postgres.

## Architecture

- `app/services/data_loader` ingestion + dataframe preparation
- `app/services/ai_classifier` Ollama client, strict JSON validation, cache writes
- `app/services/scoring` deterministic formulas and dimension weighting
- `app/services/explainability` formula narration + trust rationale payload
- `app/routes` API endpoints
- `app/models` SQLAlchemy + Pydantic models

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and update values.
4. Configure Supabase Postgres in `DATABASE_URL`.
5. Start Ollama with `llama3.2` available.

### Security-first runtime setup (recommended)

Use a least-privilege DB role for runtime instead of `postgres`.

1. Set `ADMIN_DATABASE_URL` to your admin connection string.
2. Set `APP_DB_ROLE`, `APP_DB_PASSWORD`, and `SUPABASE_PROJECT_REF`.
3. Run:

```bash
python scripts/provision_supabase_app_role.py
```

4. Copy the printed runtime URL into `DATABASE_URL`.
5. Keep `DB_AUTO_CREATE=false` in production.

`postgres` should only be used for one-time admin/provisioning tasks.

## Run

```bash
uvicorn app.main:app --reload
```

## Migrate Existing Local MySQL Data to Supabase

If you already have historical data in local MySQL, you can migrate it to Supabase.

1. Keep your target Supabase URL in `DATABASE_URL`.
2. Add your source MySQL URL in `SOURCE_MYSQL_URL`.
3. Run:

```bash
python scripts/migrate_mysql_to_supabase.py
```

The script migrates both:
- `transactions`
- `transaction_classifications`

It preserves IDs and foreign key relations, and updates Postgres sequences after migration.

## Core endpoints

- `GET /` (simple frontend dashboard)
- `GET /health`
- `POST /api/v1/transactions/ingest`
- `POST /api/v1/transactions/seed-sample`
- `POST /api/v1/transactions/classify/{user_id}`
- `POST /api/v1/trust-index/{user_id}`

`/transactions/seed-sample` is idempotent per user for seeded rows and replaces older seeded rows.

## Example ingest payload

```json
{
  "transactions": [
    {
      "user_id": "user_001",
      "transaction_ref": "tx_1001",
      "txn_date": "2026-01-05",
      "description": "Salary Credit",
      "amount": 120000,
      "direction": "income",
      "source": "bank_statement"
    },
    {
      "user_id": "user_001",
      "transaction_ref": "tx_1002",
      "txn_date": "2026-01-08",
      "description": "Rent Payment",
      "amount": 35000,
      "direction": "expense",
      "source": "bank_statement"
    }
  ]
}
```

## Trust Index formulas (deterministic)

- Cash Flow Health = `0.40*IncomeExpense + 0.35*NetSavings + 0.25*CashflowStability`
- Spending Discipline = `100*(0.40*PlannedRatio + 0.30*(1-ImpulseRatio) + 0.30*(1-SpikeFrequency))`
- Commitment Reliability = `100*(0.45*OnTime + 0.35*Consistency + 0.20*(1-MissedRatio))`
- Financial Resilience = `0.25*EmergencyBuffer + 0.25*ShockFrequency + 0.30*Recovery + 0.20*Volatility`

Dimension weights are normalized because configured weights sum to 90.
