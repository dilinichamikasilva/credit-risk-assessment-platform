"""Schemas for the flagship combined assessment (Models A + B + C)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.model_a import DefaultRiskResponse
from app.schemas.model_c import LoanAmountResponse
from ml.pipeline.features import CRIB_SCORE_MAX, CRIB_SCORE_MIN


class CombinedAssessmentRequest(BaseModel):
    """One applicant profile that can feed all three models.

    Model A uses the default-risk fields (MonthlyIncome in LKR).
    Models B and C use the loan-application fields (amounts in LKR, CRIB score).
    ``applicant_name`` is required — full assessment is always persisted.
    """

    applicant_name: str = Field(min_length=1, max_length=120)

    # --- Model A (default probability) ---
    revolving_utilization: float = Field(ge=0)
    age: int = Field(ge=18, le=120)
    times_30_59_days_late: int = Field(ge=0)
    debt_ratio: float = Field(ge=0)
    monthly_income: float = Field(ge=0, description="Monthly income in LKR")
    open_credit_lines: int = Field(ge=0)
    times_90_days_late: int = Field(ge=0)
    real_estate_loans: int = Field(ge=0)
    times_60_89_days_late: int = Field(ge=0)
    dependents: int = Field(ge=0)

    # --- Models B / C (loan application) ---
    no_of_dependents: int = Field(ge=0, le=20)
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    income_annum: float = Field(gt=0, description="Annual income in LKR")
    loan_amount: float = Field(
        gt=0,
        description="Requested loan amount (LKR) — Model B feature + Model C min() cap",
    )
    loan_term: int = Field(gt=0)
    # Official CRIB Score range 250–900 (CRIB Score Reference Guide / crib.lk FAQs)
    crib_score: int = Field(ge=CRIB_SCORE_MIN, le=CRIB_SCORE_MAX)
    residential_assets_value: float = Field(ge=0, default=0.0)
    commercial_assets_value: float = Field(ge=0, default=0.0)
    luxury_assets_value: float = Field(ge=0, default=0.0)
    bank_asset_value: float = Field(ge=0, default=0.0)

    model_config = {
        "json_schema_extra": {
            "example": {
                "applicant_name": "Demo Applicant",
                "revolving_utilization": 0.25,
                "age": 42,
                "times_30_59_days_late": 0,
                "debt_ratio": 0.28,
                "monthly_income": 150_000,
                "open_credit_lines": 5,
                "times_90_days_late": 0,
                "real_estate_loans": 1,
                "times_60_89_days_late": 0,
                "dependents": 2,
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
