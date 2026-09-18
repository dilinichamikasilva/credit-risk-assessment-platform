"""Response schemas shared across routers (health, model-info)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    models_loaded: list[str]
    models_available: list[str]


class ModelInfoEntry(BaseModel):
    model_version: str | None = None
    task: str | None = None
    metrics: dict[str, Any] = {}


class ModelInfoResponse(BaseModel):
    models: dict[str, ModelInfoEntry]
