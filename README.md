# Multi-Dimensional Trust Index (FastAPI + MySQL + Ollama)

Deterministic behavioral financial scoring with explainable 0-100 output.

## What this prototype enforces

- AI is semantic-only (category, intent, essentiality).
- AI never computes score values.
- Scoring is deterministic and formula-driven.
- All dimension details are exposed for judge-friendly explainability.
- Classification outputs are cached in MySQL.

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
4. Ensure MySQL database exists.
5. Start Ollama with `llama3.2` available.

## Run

```bash
uvicorn app.main:app --reload
```

## Core endpoints

- `GET /` (simple frontend dashboard)
- `GET /health`
- `POST /api/v1/transactions/ingest`
- `POST /api/v1/transactions/seed-sample`
- `POST /api/v1/transactions/classify/{user_id}`
- `POST /api/v1/trust-index/{user_id}`

`/transactions/seed-sample` is idempotent per user for seeded rows, replaces older seeded rows, and preloads deterministic semantic labels for seeded expenses.

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
