from __future__ import annotations

from datetime import date
from typing import Any

from app.models.schemas import TransactionIn

_SAMPLE_ROWS: list[dict[str, Any]] = [
    {
        "txn_date": "2025-11-01",
        "description": "Monthly Salary Credit",
        "amount": 120000,
        "direction": "income",
    },
    {
        "txn_date": "2025-11-03",
        "description": "House Rent Payment",
        "amount": 35000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 10,
    },
    {
        "txn_date": "2025-11-07",
        "description": "Electricity Utility Bill",
        "amount": 4700,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2025-11-08",
        "description": "Grocery Supermarket",
        "amount": 10800,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2025-11-10",
        "description": "EMI Auto Loan",
        "amount": 8000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2025-11-12",
        "description": "Credit Card Bill Payment",
        "amount": 7000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2025-11-20",
        "description": "Designer Sneakers",
        "amount": 24000,
        "direction": "expense",
        "category": "non_essential",
        "intent_label": "impulse",
        "essentiality": 1,
    },
    {
        "txn_date": "2025-11-23",
        "description": "Emergency Car Repair Towing",
        "amount": 16000,
        "direction": "expense",
        "category": "emergency",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2025-12-01",
        "description": "Monthly Salary Credit",
        "amount": 120000,
        "direction": "income",
    },
    {
        "txn_date": "2025-12-05",
        "description": "Annual Bonus Credit",
        "amount": 30000,
        "direction": "income",
    },
    {
        "txn_date": "2025-12-03",
        "description": "House Rent Payment",
        "amount": 35000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 10,
    },
    {
        "txn_date": "2025-12-08",
        "description": "Grocery Supermarket",
        "amount": 12500,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2025-12-10",
        "description": "EMI Auto Loan",
        "amount": 8000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2025-12-12",
        "description": "Credit Card Bill Payment",
        "amount": 8200,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2025-12-18",
        "description": "Holiday Gifts",
        "amount": 9500,
        "direction": "expense",
        "category": "non_essential",
        "intent_label": "planned",
        "essentiality": 3,
    },
    {
        "txn_date": "2025-12-22",
        "description": "Gaming Console Purchase",
        "amount": 32000,
        "direction": "expense",
        "category": "non_essential",
        "intent_label": "impulse",
        "essentiality": 1,
    },
    {
        "txn_date": "2026-01-01",
        "description": "Monthly Salary Credit",
        "amount": 120000,
        "direction": "income",
    },
    {
        "txn_date": "2026-01-03",
        "description": "House Rent Payment",
        "amount": 36000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 10,
    },
    {
        "txn_date": "2026-01-07",
        "description": "Electricity Utility Bill",
        "amount": 4300,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2026-01-08",
        "description": "Grocery Supermarket",
        "amount": 11200,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 9,
    },
    {
        "txn_date": "2026-01-10",
        "description": "EMI Auto Loan",
        "amount": 8000,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2026-01-12",
        "description": "Credit Card Bill Payment",
        "amount": 6800,
        "direction": "expense",
        "category": "essential",
        "intent_label": "na",
        "essentiality": 8,
    },
    {
        "txn_date": "2026-01-18",
        "description": "Restaurant Weekend",
        "amount": 5000,
        "direction": "expense",
        "category": "non_essential",
        "intent_label": "planned",
        "essentiality": 2,
    },
    {
        "txn_date": "2026-01-21",
        "description": "Luxury Watch Purchase",
        "amount": 29000,
        "direction": "expense",
        "category": "non_essential",
        "intent_label": "impulse",
        "essentiality": 1,
    },
    {
        "txn_date": "2026-01-27",
        "description": "Emergency Home Plumbing Fix",
        "amount": 11000,
        "direction": "expense",
        "category": "emergency",
        "intent_label": "na",
        "essentiality": 9,
    },
]


def _sample_transaction_ref(user_id: str, idx: int) -> str:
    return f"sample_{user_id}_{idx:04d}"


def build_sample_transactions(user_id: str) -> list[TransactionIn]:
    transactions: list[TransactionIn] = []
    for idx, row in enumerate(_SAMPLE_ROWS, start=1):
        transactions.append(
            TransactionIn(
                user_id=user_id,
                transaction_ref=_sample_transaction_ref(user_id, idx),
                txn_date=date.fromisoformat(row["txn_date"]),
                description=row["description"],
                amount=float(row["amount"]),
                direction=row["direction"],
                source="seed_dataset_v1",
            )
        )
    return transactions


def extract_months_covered(transactions: list[TransactionIn]) -> list[str]:
    months = sorted({txn.txn_date.strftime("%Y-%m") for txn in transactions})
    return months
