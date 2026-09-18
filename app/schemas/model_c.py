"""Request/response schemas for Model C — recommended loan amount."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ml.pipeline.features import CRIB_SCORE_MAX, CRIB_SCORE_MIN


class LoanAmountRequest(BaseModel):
    """Inputs for Model C.

    ``requested_amount`` is used only for the API-layer cap
    ``min(requested, predicted)`` — it is never passed into the regressor
    (Member 1's ``LoanAmountFeatures`` excludes ``loan_amount``).
    Amounts are in LKR.
    """

    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0, description="Annual income in LKR")
    loan_term: int = Field(gt=0, description="Loan term in months (matches training data)")
    # Official CRIB Score range 250–900 (CRIB Score Reference Guide / crib.lk FAQs)
    crib_score: int = Field(ge=CRIB_SCORE_MIN, le=CRIB_SCORE_MAX)
    residential_assets_value: float = Field(ge=0, default=0.0)
    commercial_assets_value: float = Field(ge=0, default=0.0)
    luxury_assets_value: float = Field(ge=0, default=0.0)
    bank_asset_value: float = Field(ge=0, default=0.0)
    requested_amount: float = Field(
        gt=0,
        description="Applicant's requested loan amount (LKR) — used for the min() cap only",
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
                "income_annum": 2_400_000,
                "loan_term": 36,
                "crib_score": 720,
                "residential_assets_value": 9_000_000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 1_500_000,
                "bank_asset_value": 1_200_000,
                "requested_amount": 3_500_000,
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
