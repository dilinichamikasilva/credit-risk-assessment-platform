from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models_db import Application
from app.schemas.applications import ApplicationDetail, ApplicationUpdate

router = APIRouter(tags=["applications"])


def _get_application_or_404(application_id: int, db: Session) -> Application:
    row = db.get(Application, application_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    return row


@router.put("/applications/{application_id}", response_model=ApplicationDetail)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
) -> ApplicationDetail:
    """Partially update an application; unset fields stay unchanged."""
    app_row = _get_application_or_404(application_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(app_row, field, value)
    db.commit()
    db.refresh(app_row)  # updated_at bump + fresh assessments list
    return ApplicationDetail.model_validate(app_row)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete an application; its assessment rows are removed by cascade."""
    app_row = _get_application_or_404(application_id, db)
    db.delete(app_row)
    db.commit()
