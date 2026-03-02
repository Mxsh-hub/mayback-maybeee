from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas import DimensionResult, ScoreRequest, TrustIndexResponse
from app.services.ai_classifier.service import AIClassificationError, AIClassifierService
from app.services.data_loader.loader import transactions_to_dataframe
from app.services.data_loader.repository import fetch_transactions_with_classification
from app.services.explainability.explainer import build_explainability_payload
from app.services.scoring.engine import compute_trust_index

router = APIRouter(prefix="/trust-index", tags=["trust-index"])


@router.post("/{user_id}", response_model=TrustIndexResponse)
def generate_trust_index(
    request: ScoreRequest = Body(default_factory=ScoreRequest),
    user_id: str = Path(min_length=1, max_length=64),
    db: Session = Depends(get_db),
) -> TrustIndexResponse:
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

    if expenses:
        classifier = AIClassifierService()
        try:
            classifier.ensure_expense_classifications(db=db, expenses=expenses)
            transactions = fetch_transactions_with_classification(
                db=db,
                user_id=user_id,
                start_date=request.start_date,
                end_date=request.end_date,
            )
        except AIClassificationError as exc:
            raise HTTPException(status_code=502, detail=f"AI classification failed: {exc}") from exc
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to persist classifications: {exc}") from exc

    frame = transactions_to_dataframe(transactions)
    score_result = compute_trust_index(frame)
    explainability = build_explainability_payload(score_result)

    dimensions = {
        name: DimensionResult(
            score=payload["score"],
            weight=payload["weight"],
            weighted_contribution=payload["weighted_contribution"],
            details=payload["details"],
        )
        for name, payload in score_result["dimensions"].items()
    }

    return TrustIndexResponse(
        user_id=user_id,
        trust_index=score_result["trust_index"],
        computed_at=datetime.utcnow(),
        tx_count=len(frame),
        dimensions=dimensions,
        explainability=explainability,
    )
