"""Analytics endpoints - read-only aggregates over applications/assessments."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_db import Application, Assessment
from app.schemas.analytics import AnalyticsSummary

router = APIRouter(tags=["analytics"])


def _count_by(db: Session, column) -> dict[str, int]:
    rows = db.execute(select(column, func.count()).group_by(column)).all()
    return {(key if key is not None else "unknown"): count for key, count in rows}


@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummary:
    total_applications = db.scalar(select(func.count()).select_from(Application)) or 0
    total_assessments = db.scalar(select(func.count()).select_from(Assessment)) or 0

    # probabilities live inside outputs JSON -> average in Python (dataset is small)
    probabilities = [
        row.outputs["probability"]
        for row in db.scalars(select(Assessment)).all()
        if isinstance(row.outputs, dict) and isinstance(row.outputs.get("probability"), (int, float))
    ]
    avg_probability = (sum(probabilities) / len(probabilities)) if probabilities else None

    return AnalyticsSummary(
        total_applications=total_applications,
        total_assessments=total_assessments,
        assessments_by_model=_count_by(db, Assessment.model_key),
        assessments_by_risk_band=_count_by(db, Assessment.risk_band),
        applications_by_status=_count_by(db, Application.status),
        avg_default_probability=avg_probability,
    )
