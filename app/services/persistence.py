"""save_assessment() helper — shared by every predict router (Model A/B/C)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models_db import Assessment, Application

def save_assessment(
    db: Session,
    *,
    model_key: str,
    model_version: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    risk_band: str | None = None,
    application_id: int | None = None,
) -> Assessment:
    """Persist one prediction run and return the row (commit included)."""
    row = Assessment(
        application_id=application_id,
        model_key=model_key,
        model_version=model_version,
        inputs=inputs,
        outputs=outputs,
        risk_band=risk_band,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_or_create_application(db: Session, *, applicant_name: str) -> Application:
    """Predict routers: link assessments to one stable applicant record."""
    row = db.query(Application).filter(Application.applicant_name == applicant_name).first()
    if row is None:
        row = Application(applicant_name=applicant_name)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row
