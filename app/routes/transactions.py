from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import (
    ClassificationRunResponse,
    IngestRequest,
    IngestResponse,
    SampleSeedRequest,
    SampleSeedResponse,
    ScoreRequest,
    TransactionDetail,
    TransactionListResponse,
)
from app.services.ai_classifier.service import AIClassificationError, AIClassifierService
from app.services.data_loader.loader import ingest_transactions
from app.services.data_loader.repository import (
    delete_seed_transactions_by_user,
    fetch_transactions_with_classification,
)
from app.services.data_loader.sample_data import (
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

        return SampleSeedResponse(
            user_id=request.user_id,
            months_covered=extract_months_covered(sample_transactions),
            transaction_count=len(sample_transactions),
            seeded_classifications=0,
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


@router.get("/user/{user_id}", response_model=TransactionListResponse)
def list_user_transactions(
    user_id: str = Path(min_length=1, max_length=64),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    try:
        transactions = fetch_transactions_with_classification(
            db=db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to read transactions: {exc}") from exc

    payload = [
        TransactionDetail(
            transaction_id=tx.id,
            user_id=tx.user_id,
            transaction_ref=tx.transaction_ref,
            txn_date=tx.txn_date,
            description=tx.description,
            amount=float(tx.amount),
            direction=tx.direction,
            source=tx.source,
            category=tx.classification.category if tx.classification else None,
            intent_label=tx.classification.intent_label if tx.classification else None,
            essentiality=int(tx.classification.essentiality) if tx.classification else None,
            model_name=tx.classification.model_name if tx.classification else None,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
            classification_updated_at=(tx.classification.updated_at if tx.classification else None),
        )
        for tx in transactions
    ]

    return TransactionListResponse(user_id=user_id, total=len(payload), transactions=payload)
