from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    applicant_name: str = Field(min_length=1, max_length=120)
    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(ge=0)
    loan_amount: float = Field(gt=0)
    loan_term: int = Field(gt=0)                                  # years
    cibil_score: int = Field(ge=300, le=900)
    residential_assets_value: float = Field(ge=0, default=0.0)
    commercial_assets_value: float = Field(ge=0, default=0.0)
    luxury_assets_value: float = Field(ge=0, default=0.0)
    bank_asset_value: float = Field(ge=0, default=0.0)


# class ApplicationUpdate(BaseModel):
#    """Partial update: send only the fields you want to change."""
#    applicant_name: str | None = Field(default=None, min_length=1, max_length=120)
#    no_of_dependents: int | None = Field(default=None, ge=0, le=20)
#    education: Literal["Graduate", "Not Graduate"] | None = None
#    self_employed: Literal["Yes", "No"] | None = None
#    income_annum: float | None = Field(default=None, ge=0)
#    loan_amount: float | None = Field(default=None, gt=0)
#    loan_term: int | None = Field(default=None, gt=0)
#    cibil_score: int | None = Field(default=None, ge=300, le=900)
#    residential_assets_value: float | None = Field(default=None, ge=0)
#    commercial_assets_value: float | None = Field(default=None, ge=0)
#    luxury_assets_value: float | None = Field(default=None, ge=0)
#    bank_asset_value: float | None = Field(default=None, ge=0)
#    status: str | None = Field(default=None, max_length=20)

class ApplicationUpdate(BaseModel):
    """Identity/reference corrections ONLY (e.g. fix a typo in the name).

    Assessment results and the loan inputs that produced them are immutable
    once assessments are logged — editing them would corrupt the audit trail.
    """
    model_config = ConfigDict(extra="forbid")  # sending cibil_score etc. -> 422

    applicant_name: str | None = Field(default=None, min_length=1, max_length=120)


class AssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None
    model_key: str
    model_version: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    risk_band: str | None
    created_at: datetime


class ApplicationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_name: str
    cibil_score: int | None
    loan_amount: float | None
    status: str
    created_at: datetime


class ApplicationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_name: str
    no_of_dependents: int
    education: str | None
    self_employed: str | None
    income_annum: float | None
    loan_amount: float | None
    loan_term: int | None
    cibil_score: int | None
    residential_assets_value: float
    commercial_assets_value: float
    luxury_assets_value: float
    bank_asset_value: float
    status: str
    created_at: datetime
    updated_at: datetime
    assessments: list[AssessmentOut] = []