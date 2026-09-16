"""Response schema for GET /analytics/summary."""
from __future__ import annotations

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_applications: int
    total_assessments: int
    assessments_by_model: dict[str, int]      # {"model_a": 12, ...}
    assessments_by_risk_band: dict[str, int]  # {"low": 8, "medium": 3, "high": 1, "unknown": 0}
    applications_by_status: dict[str, int]    # {"submitted": 5, "assessed": 2, ...}
    avg_default_probability: float | None     # mean of model_a outputs["probability"]
