"""Model B - loan approval prediction endpoint"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.model_loader import LoadedModel, ModelNotAvailableError, get_model
from app.schemas.model_b import LoanApprovalRequest, LoanApprovalResponse
from ml.pipeline.features import crib_risk_tier

router = APIRouter(tags=["model-b"])


def _get_model_b_or_503() -> LoadedModel:
    """Load Model B artifact or return a clear API error."""
    try:
        return get_model("model_b")
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/predict/loan-approval",
    response_model=LoanApprovalResponse,
    summary="Model B loan approval prediction",
)
def predict_loan_approval(
    payload: LoanApprovalRequest,
    model: LoadedModel = Depends(_get_model_b_or_503),
) -> LoanApprovalResponse:
    """Predict Approved/Rejected using the trained Model B XGBoost pipeline."""
    row = pd.DataFrame([payload.model_dump()])
    try:
        prediction = int(model.pipeline.predict(row)[0])
        probabilities = model.pipeline.predict_proba(row)[0]
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Model B could not score the supplied application: {exc}",
        ) from exc

    # The trained target is Approved=1 / Rejected=0.
    approval_probability = float(probabilities[1])
    approved = prediction == 1

    # Project-defined tiers over official CRIB 250–900 (not official CRIB letter grades).
    risk_tier = crib_risk_tier(payload.crib_score)

    return LoanApprovalResponse(
        approved=approved,
        status="Approved" if approved else "Rejected",
        approval_probability=approval_probability,
        risk_tier=risk_tier,
        model_version=model.meta.get("model_version", "model_b_unknown"),
    )
