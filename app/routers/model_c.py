"""Model C — recommended loan amount prediction endpoint (Sasuni)."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.model_loader import LoadedModel, ModelNotAvailableError, get_model
from app.schemas.model_c import LoanAmountRequest, LoanAmountResponse
from app.services.persistence import get_or_create_application, save_assessment

router = APIRouter(tags=["model-c"])

# Columns the regressor sees — never includes requested_amount / loan_amount.
_MODEL_FEATURE_COLS = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_term",
    "crib_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]


def _get_model_c_or_503() -> LoadedModel:
    try:
        return get_model("model_c")
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def recommend_amount(payload: LoanAmountRequest, model: LoadedModel) -> LoanAmountResponse:
    """Shared predict + min(requested, predicted) rule used by Model C and full-assessment."""
    features = payload.model_dump(include=set(_MODEL_FEATURE_COLS))
    row = pd.DataFrame([features])
    try:
        predicted = float(model.pipeline.predict(row)[0])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Amount prediction failed: {exc}") from exc

    if predicted < 0:
        predicted = 0.0

    recommended = min(payload.requested_amount, predicted)
    return LoanAmountResponse(
        recommended_amount=recommended,
        predicted_amount=predicted,
        capped_at_requested=recommended < predicted,
        model_version=model.meta.get("model_version", "unknown"),
    )


@router.post("/predict/recommended-amount", response_model=LoanAmountResponse)
def predict_recommended_amount(
    payload: LoanAmountRequest,
    model: LoadedModel = Depends(_get_model_c_or_503),
    db: Session = Depends(get_db),
) -> LoanAmountResponse:
    result = recommend_amount(payload, model)

    application_id = None
    if payload.applicant_name:
        app_row = get_or_create_application(db, applicant_name=payload.applicant_name)
        app_row.status = "assessed"
        # Keep thin predict records useful for the detail page when loan fields arrive.
        for field in (
            "no_of_dependents",
            "education",
            "self_employed",
            "income_annum",
            "loan_term",
            "crib_score",
            "residential_assets_value",
            "commercial_assets_value",
            "luxury_assets_value",
            "bank_asset_value",
        ):
            setattr(app_row, field, getattr(payload, field))
        app_row.loan_amount = payload.requested_amount
        db.commit()
        db.refresh(app_row)

        inputs = payload.model_dump(exclude={"applicant_name"})
        save_assessment(
            db,
            model_key="model_c",
            model_version=result.model_version,
            inputs=inputs,
            outputs=result.model_dump(exclude={"application_id"}),
            risk_band=None,
            application_id=app_row.id,
        )
        application_id = app_row.id

    result.application_id = application_id
    return result
