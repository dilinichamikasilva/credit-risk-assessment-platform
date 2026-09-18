"""Shared, versioned feature transformers used by training AND the API.

Every imputation, cap, and engineered column lives here. If a transformation
is not in this module, it does not ship.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

DEFAULT_FEATURE_LABELS = {
    "RevolvingUtilizationOfUnsecuredLines": "High credit utilisation",
    "age": "Applicant age",
    "NumberOfTime30-59DaysPastDueNotWorse": "Late payments (30-59 days)",
    "DebtRatio": "Debt-to-income ratio",
    "MonthlyIncome": "Stable monthly income",
    "NumberOfOpenCreditLinesAndLoans": "Open credit lines",
    "NumberOfTimes90DaysLate": "Severe delinquency (90+ days)",
    "NumberRealEstateLoansOrLines": "Real-estate loans",
    "NumberOfTime60-89DaysPastDueNotWorse": "Late payments (60-89 days)",
    "NumberOfDependents": "Number of dependents",
    "MonthlyDebt": "Estimated monthly debt",
    "TotalLatePayments": "Total late payments",
    "LogIncome": "Log monthly income",
    "LogDebtRatio": "Log debt-to-income ratio",
}

LOAN_FEATURE_LABELS = {
    "no_of_dependents": "Number of dependents",
    "education": "Education level",
    "self_employed": "Self-employed",
    "income_annum": "Annual income",
    "loan_amount": "Requested loan amount",
    "loan_term": "Loan term (months)",
    "crib_score": "CRIB credit score",
    "residential_assets_value": "Residential assets",
    "commercial_assets_value": "Commercial assets",
    "luxury_assets_value": "Luxury assets",
    "bank_asset_value": "Bank assets",
    "total_assets": "Total assets",
    "loan_to_income": "Loan-to-income ratio",
    "asset_coverage_ratio": "Asset coverage of the loan",
    "assets_to_income": "Assets-to-income ratio",
    "risk_tier": "CRIB risk tier (project bands)",
}

# API / notebook aliases -> canonical Give Me Some Credit names
_DEFAULT_ALIASES = {
    "revolving_utilization": "RevolvingUtilizationOfUnsecuredLines",
    "debt_ratio": "DebtRatio",
    "monthly_income": "MonthlyIncome",
    "open_credit_lines": "NumberOfOpenCreditLinesAndLoans",
    "times_90_days_late": "NumberOfTimes90DaysLate",
    "real_estate_loans": "NumberRealEstateLoansOrLines",
    "dependents": "NumberOfDependents",
    "times_30_59_days_late": "NumberOfTime30-59DaysPastDueNotWorse",
    "times_60_89_days_late": "NumberOfTime60-89DaysPastDueNotWorse",
}

DEFAULT_REQUIRED_COLS = [
    "RevolvingUtilizationOfUnsecuredLines",
    "age",
    "NumberOfTime30-59DaysPastDueNotWorse",
    "DebtRatio",
    "MonthlyIncome",
    "NumberOfOpenCreditLinesAndLoans",
    "NumberOfTimes90DaysLate",
    "NumberRealEstateLoansOrLines",
    "NumberOfTime60-89DaysPastDueNotWorse",
    "NumberOfDependents",
]

DEFAULT_OUTPUT_COLS = DEFAULT_REQUIRED_COLS + [
    "MonthlyDebt",
    "TotalLatePayments",
    "LogIncome",
    "LogDebtRatio",
]

LATE_COLS = [
    "NumberOfTime30-59DaysPastDueNotWorse",
    "NumberOfTime60-89DaysPastDueNotWorse",
    "NumberOfTimes90DaysLate",
]

LOAN_REQUIRED_COLS = [
    "no_of_dependents",
    "education",
    "self_employed",
    "income_annum",
    "loan_term",
    "crib_score",
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

ASSET_COLS = [
    "residential_assets_value",
    "commercial_assets_value",
    "luxury_assets_value",
    "bank_asset_value",
]

# Official CRIB Score range is 250–900 (CRIB Score Reference Guide / crib.lk FAQs).
CRIB_SCORE_MIN = 250
CRIB_SCORE_MAX = 900
# Project-defined Poor/Fair/Good/Excellent bands over that range — NOT official CRIB letter grades.
RISK_TIER_BINS = [249, 549, 649, 749, 900]
RISK_TIER_LABELS = ["Poor", "Fair", "Good", "Excellent"]


def crib_risk_tier(score: int | float) -> str:
    """Map a CRIB score to the project's display tier (aligned with RISK_TIER_BINS)."""
    s = int(score)
    if s <= 549:
        return "Poor"
    if s <= 649:
        return "Fair"
    if s <= 749:
        return "Good"
    return "Excellent"


def _as_frame(X) -> pd.DataFrame:
    if isinstance(X, pd.DataFrame):
        return X.copy()
    return pd.DataFrame(X).copy()


def _standardize_default_columns(X: pd.DataFrame) -> pd.DataFrame:
    rename = {col: _DEFAULT_ALIASES[col] for col in X.columns if col in _DEFAULT_ALIASES}
    if rename:
        X = X.rename(columns=rename)
    return X.loc[:, ~X.columns.duplicated()]


def strip_loan_frame(X: pd.DataFrame) -> pd.DataFrame:
    """Strip padded headers and categorical values in the loan-approval CSV."""
    X = X.copy()
    X.columns = X.columns.str.strip()
    for col in X.select_dtypes(include=["object", "string"]).columns:
        X[col] = X[col].astype("string").str.strip()
    return X


class DefaultRiskFeatures(BaseEstimator, TransformerMixin):
    """Clean GMSC-style rows and add income / delinquency features.

    Fit-time statistics (income median, late-payment medians, age median)
    are frozen so training and live scoring cannot drift.
    """

    def fit(self, X, y=None):
        X = _standardize_default_columns(_as_frame(X))
        missing = [c for c in DEFAULT_REQUIRED_COLS if c not in X.columns]
        if missing:
            raise ValueError(f"DefaultRiskFeatures missing columns: {missing}")

        self.income_median_ = float(X["MonthlyIncome"].median())
        valid_age = X.loc[X["age"] >= 18, "age"]
        self.age_median_ = float(valid_age.median() if len(valid_age) else 52)

        self.late_medians_ = {}
        for col in LATE_COLS:
            valid = X[col].replace([96, 98], np.nan)
            self.late_medians_[col] = float(valid.median())
        return self

    def transform(self, X):
        X = _standardize_default_columns(_as_frame(X))
        missing = [c for c in DEFAULT_REQUIRED_COLS if c not in X.columns]
        if missing:
            raise ValueError(f"DefaultRiskFeatures missing columns: {missing}")

        # Age 0 (and other <18) is a known GMSC data error — impute, don't clip to 18.
        X.loc[X["age"] < 18, "age"] = self.age_median_
        X["age"] = X["age"].clip(upper=100)

        X["NumberOfDependents"] = X["NumberOfDependents"].fillna(0)
        X["RevolvingUtilizationOfUnsecuredLines"] = (
            X["RevolvingUtilizationOfUnsecuredLines"].clip(lower=0, upper=2.0)
        )
        X["DebtRatio"] = X["DebtRatio"].clip(lower=0, upper=5.0)

        for col in LATE_COLS:
            X[col] = X[col].replace([96, 98], self.late_medians_[col]).clip(lower=0)

        X["MonthlyIncome"] = X["MonthlyIncome"].fillna(self.income_median_).clip(lower=0)
        X["MonthlyDebt"] = X["DebtRatio"] * X["MonthlyIncome"]
        X["TotalLatePayments"] = (
            X["NumberOfTime30-59DaysPastDueNotWorse"]
            + X["NumberOfTime60-89DaysPastDueNotWorse"]
            + X["NumberOfTimes90DaysLate"]
        )
        X["LogIncome"] = np.log1p(X["MonthlyIncome"])
        X["LogDebtRatio"] = np.log1p(X["DebtRatio"])
        return X[DEFAULT_OUTPUT_COLS]

    def get_feature_names_out(self, input_features=None):
        return np.array(DEFAULT_OUTPUT_COLS, dtype=object)


class LoanApprovalFeatures(BaseEstimator, TransformerMixin):
    """Loan-application features for approval (B) and amount (C) models.

    ``include_loan_amount_features=True`` (Model B) uses the requested amount
    as an input. Set it False for Model C so ``loan_amount`` cannot leak into
    the regression target.
    """

    def __init__(self, include_loan_amount_features: bool = True):
        self.include_loan_amount_features = include_loan_amount_features

    def fit(self, X, y=None):
        X = strip_loan_frame(_as_frame(X))
        required = list(LOAN_REQUIRED_COLS)
        if self.include_loan_amount_features:
            required.append("loan_amount")
        missing = [c for c in required if c not in X.columns]
        if missing:
            raise ValueError(f"LoanApprovalFeatures missing columns: {missing}")
        return self

    def transform(self, X):
        X = strip_loan_frame(_as_frame(X))
        required = list(LOAN_REQUIRED_COLS)
        if self.include_loan_amount_features:
            required.append("loan_amount")
        missing = [c for c in required if c not in X.columns]
        if missing:
            raise ValueError(f"LoanApprovalFeatures missing columns: {missing}")

        X["education"] = X["education"].fillna("Unknown")
        X["self_employed"] = X["self_employed"].fillna("Unknown")
        X["no_of_dependents"] = X["no_of_dependents"].fillna(0).clip(lower=0)
        X["income_annum"] = X["income_annum"].clip(lower=1)
        X["loan_term"] = X["loan_term"].clip(lower=1)
        X["crib_score"] = X["crib_score"].clip(lower=CRIB_SCORE_MIN, upper=CRIB_SCORE_MAX)

        for col in ASSET_COLS:
            X[col] = X[col].fillna(0).clip(lower=0)

        X["total_assets"] = X[ASSET_COLS].sum(axis=1)
        X["assets_to_income"] = X["total_assets"] / X["income_annum"]
        X["risk_tier"] = pd.cut(
            X["crib_score"],
            bins=RISK_TIER_BINS,
            labels=RISK_TIER_LABELS,
        ).astype("string")

        cols = [
            "no_of_dependents",
            "education",
            "self_employed",
            "income_annum",
            "loan_term",
            "crib_score",
            *ASSET_COLS,
            "total_assets",
            "assets_to_income",
            "risk_tier",
        ]
        if self.include_loan_amount_features:
            X["loan_amount"] = X["loan_amount"].clip(lower=1)
            X["loan_to_income"] = X["loan_amount"] / X["income_annum"]
            X["asset_coverage_ratio"] = X["total_assets"] / X["loan_amount"]
            cols = [
                "no_of_dependents",
                "education",
                "self_employed",
                "income_annum",
                "loan_amount",
                "loan_term",
                "crib_score",
                *ASSET_COLS,
                "total_assets",
                "loan_to_income",
                "asset_coverage_ratio",
                "risk_tier",
            ]
        return X[cols]

    def get_feature_names_out(self, input_features=None):
        if self.include_loan_amount_features:
            return np.array(
                [
                    "no_of_dependents",
                    "education",
                    "self_employed",
                    "income_annum",
                    "loan_amount",
                    "loan_term",
                    "crib_score",
                    *ASSET_COLS,
                    "total_assets",
                    "loan_to_income",
                    "asset_coverage_ratio",
                    "risk_tier",
                ],
                dtype=object,
            )
        return np.array(
            [
                "no_of_dependents",
                "education",
                "self_employed",
                "income_annum",
                "loan_term",
                "crib_score",
                *ASSET_COLS,
                "total_assets",
                "assets_to_income",
                "risk_tier",
            ],
            dtype=object,
        )


class LoanAmountFeatures(LoanApprovalFeatures):
    """Model C features: never includes requested ``loan_amount``."""

    def __init__(self):
        super().__init__(include_loan_amount_features=False)
