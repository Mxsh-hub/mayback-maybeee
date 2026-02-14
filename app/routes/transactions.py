import json

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.mysql import get_db
from app.models.schemas import (
    ClassificationRunResponse,
    IngestRequest,
    IngestResponse,
    SampleSeedRequest,
    SampleSeedResponse,
    ScoreRequest,
)
from app.services.ai_classifier.service import AIClassificationError, AIClassifierService
from app.services.ai_classifier.repository import bulk_upsert_classifications
from app.services.data_loader.loader import ingest_transactions
from app.services.data_loader.repository import (
    delete_seed_transactions_by_user,
    fetch_transactions_with_classification,
)
from app.services.data_loader.sample_data import (
    build_sample_classification_map,
    build_sample_transactions,
    extract_months_covered,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest, db: Session = Depends(get_db)) -> IngestResponse:
    try:
        result = ingest_transactions(db=db, transactions=request.transactions)
        return IngestResponse(**result)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during ingest: {exc}") from exc


@router.post("/seed-sample", response_model=SampleSeedResponse)
def seed_sample_data(
    request: SampleSeedRequest = Body(default_factory=SampleSeedRequest),
    db: Session = Depends(get_db),
) -> SampleSeedResponse:
    try:
        deleted_existing = delete_seed_transactions_by_user(db=db, user_id=request.user_id)
        sample_transactions = build_sample_transactions(user_id=request.user_id)
        ingest_result = ingest_transactions(db=db, transactions=sample_transactions)

        classification_map = build_sample_classification_map(user_id=request.user_id)
        seeded_transactions = fetch_transactions_with_classification(
            db=db,
            user_id=request.user_id,
        )

        classification_rows: list[dict] = []
        for tx in seeded_transactions:
            if tx.source != "seed_dataset_v1" or tx.direction != "expense":
                continue
            labels = classification_map.get(tx.transaction_ref)
            if labels is None:
                continue
            classification_rows.append(
                {
                    "transaction_id": tx.id,
                    "category": labels["category"],
                    "intent_label": labels["intent_label"],
                    "essentiality": labels["essentiality"],
                    "model_name": "seed_dataset_v1_manual",
                    "raw_json": json.dumps(labels, ensure_ascii=True),
                }
            )

        if classification_rows:
            bulk_upsert_classifications(db=db, records=classification_rows)

        return SampleSeedResponse(
            user_id=request.user_id,
            months_covered=extract_months_covered(sample_transactions),
            transaction_count=len(sample_transactions),
            seeded_classifications=len(classification_rows),
            deleted_existing=deleted_existing,
            **ingest_result,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed sample data: {exc}") from exc


@router.post("/classify/{user_id}", response_model=ClassificationRunResponse)
def classify_transactions(
    request: ScoreRequest = Body(default_factory=ScoreRequest),
    user_id: str = Path(min_length=1, max_length=64),
    db: Session = Depends(get_db),
) -> ClassificationRunResponse:
    try:
        transactions = fetch_transactions_with_classification(
            db=db,
            user_id=user_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read transactions: {exc}") from exc

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found for user")

    expenses = [tx for tx in transactions if tx.direction == "expense"]
    classifier = AIClassifierService()
    try:
        result = classifier.ensure_expense_classifications(db=db, expenses=expenses)
    except AIClassificationError as exc:
        raise HTTPException(status_code=502, detail=f"AI classification failed: {exc}") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to persist classifications: {exc}") from exc

    return ClassificationRunResponse(user_id=user_id, **result)
