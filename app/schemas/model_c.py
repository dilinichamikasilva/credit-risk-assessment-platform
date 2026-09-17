"""Request/response schemas for Model C — recommended loan amount."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LoanAmountRequest(BaseModel):
    """Inputs for Model C.

    ``requested_amount`` is used only for the API-layer cap
    ``min(requested, predicted)`` — it is never passed into the regressor
    (Member 1's ``LoanAmountFeatures`` excludes ``loan_amount``).
    """

    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0)
    loan_term: int = Field(gt=0, description="Loan term in months (matches training data)")
    cibil_score: int = Field(ge=300, le=900)
    residential_assets_value: float = Field(ge=0, default=0.0)
    commercial_assets_value: float = Field(ge=0, default=0.0)
    luxury_assets_value: float = Field(ge=0, default=0.0)
    bank_asset_value: float = Field(ge=0, default=0.0)
    requested_amount: float = Field(
        gt=0,
        description="Applicant's requested loan amount — used for the min() cap only",
    )
    applicant_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        description="Optional. When set, the run is saved against this applicant.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "no_of_dependents": 2,
                "education": "Graduate",
                "self_employed": "No",
                "income_annum": 9_600_000,
                "loan_term": 12,
                "cibil_score": 778,
                "residential_assets_value": 2_400_000,
                "commercial_assets_value": 17_600_000,
                "luxury_assets_value": 22_700_000,
                "bank_asset_value": 8_000_000,
                "requested_amount": 20_000_000,
                "applicant_name": "Demo Applicant",
            }
        }
    }


class LoanAmountResponse(BaseModel):
    recommended_amount: float
    predicted_amount: float
    capped_at_requested: bool
    model_version: str
    application_id: int | None = None
