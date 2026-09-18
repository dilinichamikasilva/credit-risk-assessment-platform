"""Model B - loan approval prediction API schemas"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class LoanApprovalRequest(BaseModel):
    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0)
    loan_amount: float = Field(gt=0)
    loan_term: int = Field(gt=0)
    cibil_score: int = Field(ge=300, le=900)
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
                "income_annum": 5000000,
                "loan_amount": 15000000,
                "loan_term": 240,
                "cibil_score": 750,
                "residential_assets_value": 10000000,
                "commercial_assets_value": 5000000,
                "luxury_assets_value": 2000000,
                "bank_asset_value": 3000000,
            }
        }
    }


class LoanApprovalResponse(BaseModel):
    approved: bool
    status: Literal["Approved", "Rejected"]
    approval_probability: float
    risk_tier: Literal["Poor", "Fair", "Good", "Excellent"]
    model_version: str
