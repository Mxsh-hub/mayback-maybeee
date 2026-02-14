from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionIn(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    transaction_ref: str | None = Field(default=None, max_length=128)
    txn_date: date
    description: str = Field(min_length=1, max_length=512)
    amount: float = Field(gt=0)
    direction: Literal["income", "expense"]
    source: str | None = Field(default=None, max_length=64)

    @field_validator("user_id", "description", "source", mode="before")
    @classmethod
    def trim_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()


class IngestRequest(BaseModel):
    transactions: list[TransactionIn] = Field(min_length=1)


class IngestResponse(BaseModel):
    received: int
    inserted: int
    updated: int


class ScoreRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


class ClassificationRunResponse(BaseModel):
    user_id: str
    scanned_expenses: int
    newly_classified: int
    already_cached: int


class SampleSeedRequest(BaseModel):
    user_id: str = Field(default="demo_user_001", min_length=1, max_length=64)


class SampleSeedResponse(BaseModel):
    user_id: str
    months_covered: list[str]
    transaction_count: int
    seeded_classifications: int
    deleted_existing: int
    received: int
    inserted: int
    updated: int


class DimensionResult(BaseModel):
    score: float
    weight: float
    weighted_contribution: float
    details: dict[str, Any]


class TrustIndexResponse(BaseModel):
    user_id: str
    trust_index: float
    computed_at: datetime
    tx_count: int
    dimensions: dict[str, DimensionResult]
    explainability: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
