import numpy as np
import pandas as pd

from ml.pipeline.features import DefaultRiskFeatures, LoanAmountFeatures, LoanApprovalFeatures


def _default_sample():
    return pd.DataFrame(
        {
            "RevolvingUtilizationOfUnsecuredLines": [0.2, 1.5, 50.0],
            "age": [45, 0, 61],
            "NumberOfTime30-59DaysPastDueNotWorse": [0, 98, 1],
            "DebtRatio": [0.3, 0.8, 200.0],
            "MonthlyIncome": [5000.0, np.nan, 8000.0],
            "NumberOfOpenCreditLinesAndLoans": [6, 3, 8],
            "NumberOfTimes90DaysLate": [0, 98, 0],
            "NumberRealEstateLoansOrLines": [1, 0, 2],
            "NumberOfTime60-89DaysPastDueNotWorse": [0, 98, 0],
            "NumberOfDependents": [2.0, np.nan, 0.0],
        }
    )


def _loan_sample():
    return pd.DataFrame(
        {
            "loan_id": [1, 2],
            " no_of_dependents": [1, 0],
            " education": [" Graduate", " Not Graduate"],
            " self_employed": [" No", " Yes"],
            "income_annum": [5_000_000, 3_000_000],
            "loan_amount": [10_000_000, 4_000_000],
            "loan_term": [12, 8],
            "cibil_score": [780, 420],
            "residential_assets_value": [-100000, 1_000_000],
            "commercial_assets_value": [500_000, 0],
            "luxury_assets_value": [2_000_000, 800_000],
            "bank_asset_value": [700_000, 200_000],
        }
    )


def test_default_features_idempotent():
    sample_df = _default_sample()
    feat = DefaultRiskFeatures().fit(sample_df)
    out1 = feat.transform(sample_df)
    out2 = feat.transform(sample_df)
    pd.testing.assert_frame_equal(out1, out2)


def test_no_nans_after_transform():
    out = DefaultRiskFeatures().fit(_default_sample()).transform(_default_sample())
    assert out["MonthlyIncome"].isna().sum() == 0
    assert out.isna().sum().sum() == 0


def test_default_caps_and_sentinels():
    out = DefaultRiskFeatures().fit(_default_sample()).transform(_default_sample())
    assert out["RevolvingUtilizationOfUnsecuredLines"].max() <= 2.0
    assert out["DebtRatio"].max() <= 5.0
    assert (out["NumberOfTimes90DaysLate"] == 98).sum() == 0
    assert out["age"].min() >= 18


def test_default_accepts_api_aliases():
    raw = _default_sample().rename(
        columns={
            "RevolvingUtilizationOfUnsecuredLines": "revolving_utilization",
            "DebtRatio": "debt_ratio",
            "MonthlyIncome": "monthly_income",
            "NumberOfOpenCreditLinesAndLoans": "open_credit_lines",
            "NumberOfTimes90DaysLate": "times_90_days_late",
            "NumberRealEstateLoansOrLines": "real_estate_loans",
            "NumberOfDependents": "dependents",
        }
    )
    feat = DefaultRiskFeatures().fit(_default_sample())
    out = feat.transform(raw)
    assert list(out.columns) == list(feat.transform(_default_sample()).columns)


def test_loan_strips_headers_and_clips_assets():
    feat = LoanApprovalFeatures().fit(_loan_sample())
    out = feat.transform(_loan_sample())
    assert "education" in out.columns
    assert set(out["education"]) <= {"Graduate", "Not Graduate"}
    assert out["residential_assets_value"].min() >= 0
    assert out["risk_tier"].tolist() == ["Excellent", "Poor"]
    assert out.isna().sum().sum() == 0


def test_loan_features_idempotent():
    sample = _loan_sample()
    feat = LoanApprovalFeatures().fit(sample)
    pd.testing.assert_frame_equal(feat.transform(sample), feat.transform(sample))


def test_amount_features_do_not_leak_loan_amount():
    out = LoanAmountFeatures().fit(_loan_sample()).transform(_loan_sample())
    assert "loan_amount" not in out.columns
    assert "loan_to_income" not in out.columns
    assert "asset_coverage_ratio" not in out.columns
    assert "total_assets" in out.columns
