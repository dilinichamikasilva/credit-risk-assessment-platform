"""Health check and model-info endpoints (shared scaffolding)."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import MODEL_FILES
from app.model_loader import ModelNotAvailableError, available_models, get_model
from app.schemas.common import HealthResponse, ModelInfoEntry, ModelInfoResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    available = available_models()
    loaded = []
    for key in available:
        try:
            get_model(key)
            loaded.append(key)
        except ModelNotAvailableError:
            continue
    return HealthResponse(
        status="ok" if loaded else "degraded",
        models_loaded=loaded,
        models_available=available,
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    entries: dict[str, ModelInfoEntry] = {}
    for key in MODEL_FILES:
        try:
            loaded = get_model(key)
        except ModelNotAvailableError:
            continue
        entries[key] = ModelInfoEntry(
            model_version=loaded.meta.get("model_version"),
            task=loaded.meta.get("task"),
            metrics=loaded.meta.get("metrics", {}),
        )
    return ModelInfoResponse(models=entries)
