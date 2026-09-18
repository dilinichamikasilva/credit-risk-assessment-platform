"""Model B - loan approval prediction API schemas"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from ml.pipeline.features import CRIB_SCORE_MAX, CRIB_SCORE_MIN


class LoanApprovalRequest(BaseModel):
    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    # Annual income in LKR (mid-2020s retail band; see Phase 0 research)
    income_annum: float = Field(gt=0, description="Annual income in LKR")
    loan_amount: float = Field(gt=0, description="Requested loan amount in LKR")
    loan_term: int = Field(gt=0)
    # Official CRIB Score range 250–900 (CRIB Score Reference Guide / crib.lk FAQs)
    crib_score: int = Field(ge=CRIB_SCORE_MIN, le=CRIB_SCORE_MAX)
    residential_assets_value: float = Field(ge=0)
    commercial_assets_value: float = Field(ge=0)
    luxury_assets_value: float = Field(ge=0)
    bank_asset_value: float = Field(ge=0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "no_of_dependents": 2,
                "education": "Graduate",
                "self_employed": "No",
                "income_annum": 1_800_000,
                "loan_amount": 2_500_000,
                "loan_term": 36,
                "crib_score": 720,
                "residential_assets_value": 8_000_000,
                "commercial_assets_value": 0,
                "luxury_assets_value": 1_200_000,
                "bank_asset_value": 900_000,
            }
        }
    }


class LoanApprovalResponse(BaseModel):
    approved: bool
    status: Literal["Approved", "Rejected"]
    approval_probability: float
    risk_tier: Literal["Poor", "Fair", "Good", "Excellent"]
    model_version: str
