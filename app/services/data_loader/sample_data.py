from __future__ import annotations

from datetime import date
from typing import Any

from app.models.schemas import TransactionIn

_PROFILE_ROWS: dict[str, list[dict[str, Any]]] = {
    "salaried_professional": [
        {"txn_date": "2025-11-01", "description": "Salary Credit - Tech Solutions Pvt Ltd", "amount": 128000, "direction": "income"},
        {"txn_date": "2025-11-03", "description": "Apartment Rent - Green Heights", "amount": 38000, "direction": "expense"},
        {"txn_date": "2025-11-05", "description": "UPI Grocery - Fresh Basket", "amount": 9400, "direction": "expense"},
        {"txn_date": "2025-11-08", "description": "Electricity Bill - BESCOM", "amount": 4200, "direction": "expense"},
        {"txn_date": "2025-11-10", "description": "Home Loan EMI - HDFC", "amount": 26500, "direction": "expense"},
        {"txn_date": "2025-11-14", "description": "Internet + Mobile Plan", "amount": 2100, "direction": "expense"},
        {"txn_date": "2025-11-19", "description": "Team Dinner - Midtown Bistro", "amount": 4600, "direction": "expense"},
        {"txn_date": "2025-11-23", "description": "Noise Cancelling Headphones", "amount": 17999, "direction": "expense"},
        {"txn_date": "2025-12-01", "description": "Salary Credit - Tech Solutions Pvt Ltd", "amount": 128000, "direction": "income"},
        {"txn_date": "2025-12-05", "description": "Year-end Performance Bonus", "amount": 42000, "direction": "income"},
        {"txn_date": "2025-12-03", "description": "Apartment Rent - Green Heights", "amount": 38000, "direction": "expense"},
        {"txn_date": "2025-12-06", "description": "UPI Grocery - Fresh Basket", "amount": 10350, "direction": "expense"},
        {"txn_date": "2025-12-09", "description": "Electricity Bill - BESCOM", "amount": 4800, "direction": "expense"},
        {"txn_date": "2025-12-10", "description": "Home Loan EMI - HDFC", "amount": 26500, "direction": "expense"},
        {"txn_date": "2025-12-15", "description": "Medical Consultation - Apollo", "amount": 3600, "direction": "expense"},
        {"txn_date": "2025-12-21", "description": "Holiday Flight Ticket", "amount": 22600, "direction": "expense"},
        {"txn_date": "2026-01-01", "description": "Salary Credit - Tech Solutions Pvt Ltd", "amount": 128000, "direction": "income"},
        {"txn_date": "2026-01-03", "description": "Apartment Rent - Green Heights", "amount": 39000, "direction": "expense"},
        {"txn_date": "2026-01-06", "description": "UPI Grocery - Fresh Basket", "amount": 9700, "direction": "expense"},
        {"txn_date": "2026-01-08", "description": "Electricity Bill - BESCOM", "amount": 4300, "direction": "expense"},
        {"txn_date": "2026-01-10", "description": "Home Loan EMI - HDFC", "amount": 26500, "direction": "expense"},
        {"txn_date": "2026-01-13", "description": "Car Service and Repair", "amount": 11800, "direction": "expense"},
        {"txn_date": "2026-01-18", "description": "Weekend Cafe + Movies", "amount": 3900, "direction": "expense"},
        {"txn_date": "2026-01-24", "description": "Smartwatch Purchase", "amount": 14900, "direction": "expense"},
    ],
    "freelancer_variable_cashflow": [
        {"txn_date": "2025-11-02", "description": "Client Payment - UI Redesign", "amount": 68000, "direction": "income"},
        {"txn_date": "2025-11-04", "description": "Coworking Desk Rent", "amount": 9500, "direction": "expense"},
        {"txn_date": "2025-11-07", "description": "Cloud Tools Subscription", "amount": 2800, "direction": "expense"},
        {"txn_date": "2025-11-11", "description": "Ad-hoc Equipment Upgrade", "amount": 12500, "direction": "expense"},
        {"txn_date": "2025-11-15", "description": "Health Insurance Premium", "amount": 6200, "direction": "expense"},
        {"txn_date": "2025-11-20", "description": "Client Payment - API Integration", "amount": 52000, "direction": "income"},
        {"txn_date": "2025-11-23", "description": "Emergency Dental Procedure", "amount": 14600, "direction": "expense"},
        {"txn_date": "2025-11-27", "description": "Online Course Bundle", "amount": 4300, "direction": "expense"},
        {"txn_date": "2025-12-03", "description": "Client Payment - Analytics Dashboard", "amount": 74000, "direction": "income"},
        {"txn_date": "2025-12-06", "description": "Coworking Desk Rent", "amount": 9500, "direction": "expense"},
        {"txn_date": "2025-12-09", "description": "Cloud Tools Subscription", "amount": 2900, "direction": "expense"},
        {"txn_date": "2025-12-12", "description": "Laptop Repair - Motherboard", "amount": 19800, "direction": "expense"},
        {"txn_date": "2025-12-18", "description": "Client Payment - Landing Page Sprint", "amount": 46000, "direction": "income"},
        {"txn_date": "2025-12-22", "description": "Family Grocery and Essentials", "amount": 8900, "direction": "expense"},
        {"txn_date": "2025-12-29", "description": "Travel Booking - New Year", "amount": 16000, "direction": "expense"},
        {"txn_date": "2026-01-04", "description": "Client Payment - Mobile App Prototype", "amount": 82000, "direction": "income"},
        {"txn_date": "2026-01-07", "description": "Coworking Desk Rent", "amount": 9500, "direction": "expense"},
        {"txn_date": "2026-01-10", "description": "Cloud Tools Subscription", "amount": 3050, "direction": "expense"},
        {"txn_date": "2026-01-13", "description": "Advance Tax Payment", "amount": 17500, "direction": "expense"},
        {"txn_date": "2026-01-16", "description": "Client Payment - Performance Audit", "amount": 39000, "direction": "income"},
        {"txn_date": "2026-01-19", "description": "Medical Lab Tests", "amount": 5400, "direction": "expense"},
        {"txn_date": "2026-01-24", "description": "Studio Lighting Purchase", "amount": 11900, "direction": "expense"},
        {"txn_date": "2026-01-27", "description": "Client Payment - Maintenance Retainer", "amount": 21000, "direction": "income"},
    ],
    "small_business_owner": [
        {"txn_date": "2025-11-01", "description": "Store Sales Settlement - POS", "amount": 154000, "direction": "income"},
        {"txn_date": "2025-11-03", "description": "Shop Rent - Commercial Unit", "amount": 42000, "direction": "expense"},
        {"txn_date": "2025-11-05", "description": "Wholesale Inventory Purchase", "amount": 53000, "direction": "expense"},
        {"txn_date": "2025-11-08", "description": "Staff Salaries Transfer", "amount": 36000, "direction": "expense"},
        {"txn_date": "2025-11-11", "description": "Utility Bill - Store + Warehouse", "amount": 9800, "direction": "expense"},
        {"txn_date": "2025-11-15", "description": "Business Loan EMI", "amount": 18500, "direction": "expense"},
        {"txn_date": "2025-11-19", "description": "Festival Sales Settlement", "amount": 88000, "direction": "income"},
        {"txn_date": "2025-11-24", "description": "Freezer Unit Emergency Repair", "amount": 22300, "direction": "expense"},
        {"txn_date": "2025-12-01", "description": "Store Sales Settlement - POS", "amount": 161000, "direction": "income"},
        {"txn_date": "2025-12-03", "description": "Shop Rent - Commercial Unit", "amount": 42000, "direction": "expense"},
        {"txn_date": "2025-12-05", "description": "Wholesale Inventory Purchase", "amount": 61000, "direction": "expense"},
        {"txn_date": "2025-12-08", "description": "Staff Salaries Transfer", "amount": 37000, "direction": "expense"},
        {"txn_date": "2025-12-10", "description": "Utility Bill - Store + Warehouse", "amount": 10700, "direction": "expense"},
        {"txn_date": "2025-12-14", "description": "Marketing Campaign Spend", "amount": 12800, "direction": "expense"},
        {"txn_date": "2025-12-20", "description": "Corporate Bulk Order Settlement", "amount": 72000, "direction": "income"},
        {"txn_date": "2025-12-26", "description": "Premium Coffee Machine Upgrade", "amount": 27400, "direction": "expense"},
        {"txn_date": "2026-01-01", "description": "Store Sales Settlement - POS", "amount": 149500, "direction": "income"},
        {"txn_date": "2026-01-03", "description": "Shop Rent - Commercial Unit", "amount": 43500, "direction": "expense"},
        {"txn_date": "2026-01-05", "description": "Wholesale Inventory Purchase", "amount": 48800, "direction": "expense"},
        {"txn_date": "2026-01-08", "description": "Staff Salaries Transfer", "amount": 36500, "direction": "expense"},
        {"txn_date": "2026-01-11", "description": "Utility Bill - Store + Warehouse", "amount": 9600, "direction": "expense"},
        {"txn_date": "2026-01-15", "description": "Business Loan EMI", "amount": 18500, "direction": "expense"},
        {"txn_date": "2026-01-18", "description": "Insurance Claim Credit", "amount": 18500, "direction": "income"},
        {"txn_date": "2026-01-23", "description": "Cold Storage Compressor Fix", "amount": 17100, "direction": "expense"},
    ],
}

_USER_PROFILE_MAP = {
    "demo_user_001": "salaried_professional",
    "demo_user_002": "freelancer_variable_cashflow",
    "demo_user_003": "small_business_owner",
}


def _sample_transaction_ref(user_id: str, idx: int) -> str:
    return f"sample_{user_id}_{idx:04d}"


def _resolve_profile(user_id: str) -> str:
    if user_id in _USER_PROFILE_MAP:
        return _USER_PROFILE_MAP[user_id]

    profiles = sorted(_PROFILE_ROWS.keys())
    bucket = sum(ord(ch) for ch in user_id) % len(profiles)
    return profiles[bucket]


def build_sample_transactions(user_id: str) -> list[TransactionIn]:
    profile_name = _resolve_profile(user_id)
    rows = _PROFILE_ROWS[profile_name]

    transactions: list[TransactionIn] = []
    for idx, row in enumerate(rows, start=1):
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
