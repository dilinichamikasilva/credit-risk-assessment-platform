"""Flagship endpoint: run Models A + B + C together and always persist (Sasuni)."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.model_loader import LoadedModel, ModelNotAvailableError, get_model
from app.routers.model_a import _risk_band
from app.routers.model_c import recommend_amount
from app.schemas.assessment import (
    CombinedAssessmentRequest,
    CombinedAssessmentResponse,
    LoanApprovalSlice,
)
from app.schemas.model_a import DefaultRiskResponse
from app.schemas.model_c import LoanAmountRequest
from app.services.persistence import get_or_create_application, save_assessment

router = APIRouter(tags=["assessment"])


def _require_models() -> tuple[LoadedModel, LoadedModel, LoadedModel]:
    missing: list[str] = []
    loaded: dict[str, LoadedModel] = {}
    for key in ("model_a", "model_b", "model_c"):
        try:
            loaded[key] = get_model(key)
        except ModelNotAvailableError:
            missing.append(key)
    if missing:
        raise HTTPException(
            status_code=503,
            detail=f"Full assessment needs all three models; missing: {', '.join(missing)}",
        )
    return loaded["model_a"], loaded["model_b"], loaded["model_c"]


def _score_default(payload: CombinedAssessmentRequest, model: LoadedModel) -> DefaultRiskResponse:
    row = pd.DataFrame(
        [
            {
                "revolving_utilization": payload.revolving_utilization,
                "age": payload.age,
                "times_30_59_days_late": payload.times_30_59_days_late,
                "debt_ratio": payload.debt_ratio,
                "monthly_income": payload.monthly_income,
                "open_credit_lines": payload.open_credit_lines,
                "times_90_days_late": payload.times_90_days_late,
                "real_estate_loans": payload.real_estate_loans,
                "times_60_89_days_late": payload.times_60_89_days_late,
                "dependents": payload.dependents,
            }
        ]
    )
    try:
        probability = float(model.pipeline.predict_proba(row)[:, 1][0])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Default scoring failed: {exc}") from exc
    return DefaultRiskResponse(
        probability=probability,
        risk_band=_risk_band(probability, model.meta.get("risk_bands", {})),
        model_version=model.meta.get("model_version", "unknown"),
    )


def _score_approval(payload: CombinedAssessmentRequest, model: LoadedModel) -> LoanApprovalSlice:
    row = pd.DataFrame(
        [
            {
                "no_of_dependents": payload.no_of_dependents,
                "education": payload.education,
                "self_employed": payload.self_employed,
                "income_annum": payload.income_annum,
                "loan_amount": payload.loan_amount,
                "loan_term": payload.loan_term,
                "crib_score": payload.crib_score,
                "residential_assets_value": payload.residential_assets_value,
                "commercial_assets_value": payload.commercial_assets_value,
                "luxury_assets_value": payload.luxury_assets_value,
                "bank_asset_value": payload.bank_asset_value,
            }
        ]
    )
    try:
        approval_probability = float(model.pipeline.predict_proba(row)[:, 1][0])
        approved = bool(model.pipeline.predict(row)[0] == 1)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Approval scoring failed: {exc}") from exc
    return LoanApprovalSlice(
        approved=approved,
        approval_probability=approval_probability,
        model_version=model.meta.get("model_version", "unknown"),
    )


@router.post("/predict/full-assessment", response_model=CombinedAssessmentResponse)
def predict_full_assessment(
    payload: CombinedAssessmentRequest,
    db: Session = Depends(get_db),
) -> CombinedAssessmentResponse:
    model_a, model_b, model_c = _require_models()

    default = _score_default(payload, model_a)
    approval = _score_approval(payload, model_b)
    amount_req = LoanAmountRequest(
        no_of_dependents=payload.no_of_dependents,
        education=payload.education,
        self_employed=payload.self_employed,
        income_annum=payload.income_annum,
        loan_term=payload.loan_term,
        crib_score=payload.crib_score,
        residential_assets_value=payload.residential_assets_value,
        commercial_assets_value=payload.commercial_assets_value,
        luxury_assets_value=payload.luxury_assets_value,
        bank_asset_value=payload.bank_asset_value,
        requested_amount=payload.loan_amount,
    )
    amount = recommend_amount(amount_req, model_c)

    app_row = get_or_create_application(db, applicant_name=payload.applicant_name)
    app_row.status = "assessed"
    for field in (
        "no_of_dependents",
        "education",
        "self_employed",
        "income_annum",
        "loan_amount",
        "loan_term",
        "crib_score",
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value",
    ):
        setattr(app_row, field, getattr(payload, field))
    db.commit()
    db.refresh(app_row)

    save_assessment(
        db,
        model_key="model_a",
        model_version=default.model_version,
        inputs={
            "revolving_utilization": payload.revolving_utilization,
            "age": payload.age,
            "times_30_59_days_late": payload.times_30_59_days_late,
            "debt_ratio": payload.debt_ratio,
            "monthly_income": payload.monthly_income,
            "open_credit_lines": payload.open_credit_lines,
            "times_90_days_late": payload.times_90_days_late,
            "real_estate_loans": payload.real_estate_loans,
            "times_60_89_days_late": payload.times_60_89_days_late,
            "dependents": payload.dependents,
        },
        outputs=default.model_dump(),
        risk_band=default.risk_band,
        application_id=app_row.id,
    )
    save_assessment(
        db,
        model_key="model_b",
        model_version=approval.model_version,
        inputs={
            "no_of_dependents": payload.no_of_dependents,
            "education": payload.education,
            "self_employed": payload.self_employed,
            "income_annum": payload.income_annum,
            "loan_amount": payload.loan_amount,
            "loan_term": payload.loan_term,
            "crib_score": payload.crib_score,
            "residential_assets_value": payload.residential_assets_value,
            "commercial_assets_value": payload.commercial_assets_value,
            "luxury_assets_value": payload.luxury_assets_value,
            "bank_asset_value": payload.bank_asset_value,
        },
        outputs=approval.model_dump(),
        risk_band=None,
        application_id=app_row.id,
    )
    amount.application_id = app_row.id
    save_assessment(
        db,
        model_key="model_c",
        model_version=amount.model_version,
        inputs=amount_req.model_dump(),
        outputs=amount.model_dump(exclude={"application_id"}),
        risk_band=None,
        application_id=app_row.id,
    )

    return CombinedAssessmentResponse(
        application_id=app_row.id,
        default=default,
        approval=approval,
        amount=amount,
    )
