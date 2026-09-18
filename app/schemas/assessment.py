"""Schemas for the flagship combined assessment (Models A + B + C)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.model_a import DefaultRiskResponse
from app.schemas.model_c import LoanAmountResponse


class CombinedAssessmentRequest(BaseModel):
    """One applicant profile that can feed all three models.

    Model A uses the GMSC-style default-risk fields.
    Models B and C use the loan-application fields.
    ``applicant_name`` is required — full assessment is always persisted.
    """

    applicant_name: str = Field(min_length=1, max_length=120)

    # --- Model A (default probability) ---
    revolving_utilization: float = Field(ge=0)
    age: int = Field(ge=18, le=120)
    times_30_59_days_late: int = Field(ge=0)
    debt_ratio: float = Field(ge=0)
    monthly_income: float = Field(ge=0)
    open_credit_lines: int = Field(ge=0)
    times_90_days_late: int = Field(ge=0)
    real_estate_loans: int = Field(ge=0)
    times_60_89_days_late: int = Field(ge=0)
    dependents: int = Field(ge=0)

    # --- Models B / C (loan application) ---
    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0)
    loan_amount: float = Field(
        gt=0,
        description="Requested loan amount — Model B feature + Model C min() cap",
    )
    loan_term: int = Field(gt=0)
    cibil_score: int = Field(ge=300, le=900)
    residential_assets_value: float = Field(ge=0, default=0.0)
    commercial_assets_value: float = Field(ge=0, default=0.0)
    luxury_assets_value: float = Field(ge=0, default=0.0)
    bank_asset_value: float = Field(ge=0, default=0.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "applicant_name": "Demo Applicant",
                "revolving_utilization": 0.3,
                "age": 45,
                "times_30_59_days_late": 0,
                "debt_ratio": 0.35,
                "monthly_income": 5000,
                "open_credit_lines": 6,
                "times_90_days_late": 0,
                "real_estate_loans": 1,
                "times_60_89_days_late": 0,
                "dependents": 2,
                "no_of_dependents": 2,
                "education": "Graduate",
                "self_employed": "No",
                "income_annum": 9_600_000,
                "loan_amount": 20_000_000,
                "loan_term": 12,
                "cibil_score": 778,
                "residential_assets_value": 2_400_000,
                "commercial_assets_value": 17_600_000,
                "luxury_assets_value": 22_700_000,
                "bank_asset_value": 8_000_000,
            }
        }
    }


class LoanApprovalSlice(BaseModel):
    """Inline Model B result embedded in the combined response."""

    approved: bool
    approval_probability: float
    model_version: str


class CombinedAssessmentResponse(BaseModel):
    application_id: int
    default: DefaultRiskResponse
    approval: LoanApprovalSlice
    amount: LoanAmountResponse
