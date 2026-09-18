"""Request/response schemas for Model A - default probability."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DefaultRiskRequest(BaseModel):
    revolving_utilization: float = Field(
        ge=0, description="Total balance on credit lines / credit limits"
    )
    age: int = Field(ge=0, le=120)
    times_30_59_days_late: int = Field(ge=0, alias="times_30_59_days_late")
    debt_ratio: float = Field(ge=0)
    # Monthly income in LKR (mid-2020s retail; see Phase 0 / synthetic dataset notes)
    monthly_income: float = Field(ge=0, description="Monthly income in LKR")
    open_credit_lines: int = Field(ge=0)
    times_90_days_late: int = Field(ge=0)
    real_estate_loans: int = Field(ge=0)
    times_60_89_days_late: int = Field(ge=0)
    dependents: int = Field(ge=0)

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
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
            }
        },
    }


class DefaultRiskResponse(BaseModel):
    probability: float
    risk_band: Literal["low", "medium", "high"]
    model_version: str
