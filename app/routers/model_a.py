"""Model A - default probability prediction endpoint."""
from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from app.model_loader import LoadedModel, ModelNotAvailableError, get_model_a
from app.schemas.model_a import DefaultRiskRequest, DefaultRiskResponse

router = APIRouter(tags=["model-a"])


def _risk_band(probability: float, risk_bands: dict) -> str:
    low_lt = risk_bands.get("low_lt", 0.10)
    medium_lt = risk_bands.get("medium_lt", 0.35)
    if probability < low_lt:
        return "low"
    if probability < medium_lt:
        return "medium"
    return "high"


def _get_model_a_or_503() -> LoadedModel:
    try:
        return get_model_a()
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/predict/default-probability", response_model=DefaultRiskResponse)
def predict_default_probability(
    payload: DefaultRiskRequest,
    model: LoadedModel = Depends(_get_model_a_or_503),
) -> DefaultRiskResponse:
    row = pd.DataFrame([payload.model_dump(by_alias=True)])
    probability = float(model.pipeline.predict_proba(row)[:, 1][0])
    risk_bands = model.meta.get("risk_bands", {})
    return DefaultRiskResponse(
        probability=probability,
        risk_band=_risk_band(probability, risk_bands),
        model_version=model.meta.get("model_version", "unknown"),
    )
