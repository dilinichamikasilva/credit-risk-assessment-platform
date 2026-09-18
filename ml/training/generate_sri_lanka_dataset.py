"""Generate synthetic Sri Lankan credit/loan CSVs calibrated to Phase 0 research.

SYNTHETIC DATA — not real applicant records.
Calibrated to:
  - CRIB Score range 250–900 (CRIB Score Reference Guide / crib.lk FAQs)
  - DCS HIES 2019 household income anchors (nominal mid-2020s retail bands)
See reports/phase0_sri_lanka_research.md.

Usage:
  python -m ml.training.generate_sri_lanka_dataset
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from ml.config import DATA_RAW, RANDOM_STATE, REPORTS_DIR, ensure_dirs

PROVENANCE = (
    "synthetic, calibrated to CRIB Score range 250-900 (crib.lk Score Reference Guide / FAQs) "
    "and DCS HIES 2019 household income anchors (mean monthly LKR 76,414) with mid-2020s "
    "nominal retail loan/asset bands — NOT real applicant records. "
    "See reports/phase0_sri_lanka_research.md."
)

N_DEFAULT = 40_000
N_LOAN = 6_000


def _rng(seed: int = RANDOM_STATE) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate_default_risk(n: int = N_DEFAULT, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Model A — consumer delinquency proxy (SeriousDlqin2yrs-compatible columns).

    MonthlyIncome in LKR. Default label from a multi-factor latent score + noise
    (utilisation, late payments, debt ratio, income) — not a single hard rule.
    """
    rng = _rng(seed)
    # Mid-2020s nominal monthly income (LKR): lognormal around ~90k, fat right tail
    monthly_income = np.clip(rng.lognormal(mean=11.35, sigma=0.55, size=n), 25_000, 1_200_000)
    age = np.clip(rng.normal(42, 12, n).astype(int), 21, 75)
    dependents = rng.choice([0, 1, 2, 3, 4, 5], size=n, p=[0.28, 0.30, 0.22, 0.12, 0.06, 0.02])

    util = np.clip(rng.beta(1.2, 3.5, n) * 1.4, 0, 2.0)
    # Some extreme util outliers like real credit data
    util = np.where(rng.random(n) < 0.02, rng.uniform(1.5, 2.0, n), util)

    debt_ratio = np.clip(rng.lognormal(mean=-0.8, sigma=0.7, size=n), 0.01, 5.0)
    open_lines = np.clip(rng.poisson(5, n), 0, 25)
    re_loans = np.clip(rng.poisson(0.6, n), 0, 6)

    late_30 = np.clip(rng.poisson(0.35, n), 0, 12)
    late_60 = np.clip(rng.poisson(0.15, n), 0, 8)
    late_90 = np.clip(rng.poisson(0.10, n), 0, 8)
    # Rare sentinel-like spikes (will be cleaned in pipeline)
    spike = rng.random(n) < 0.004
    late_30 = np.where(spike, 98, late_30)
    late_60 = np.where(spike, 98, late_60)
    late_90 = np.where(spike, 98, late_90)

    # ~8% missing income (common in retail applications)
    income_out = monthly_income.copy()
    income_out[rng.random(n) < 0.08] = np.nan
    dep_out = dependents.astype(float)
    dep_out[rng.random(n) < 0.03] = np.nan

    # Latent default risk (multi-factor) — target rate ~8–12%, separable enough to learn
    z = (
        2.4 * util
        + 1.2 * np.log1p(debt_ratio)
        + 0.7 * np.minimum(late_30, 10)
        + 1.1 * np.minimum(late_60, 8)
        + 1.4 * np.minimum(late_90, 8)
        - 0.55 * np.log1p(monthly_income / 80_000)
        - 0.02 * (age - 40)
        + 0.12 * dependents
        + rng.normal(0, 0.55, n)
    )
    p_default = 1 / (1 + np.exp(-(z - 2.8)))
    y = (rng.random(n) < p_default).astype(int)

    df = pd.DataFrame(
        {
            "Id": np.arange(1, n + 1),
            "SeriousDlqin2yrs": y,
            "RevolvingUtilizationOfUnsecuredLines": util,
            "age": age,
            "NumberOfTime30-59DaysPastDueNotWorse": late_30,
            "DebtRatio": debt_ratio,
            "MonthlyIncome": income_out,
            "NumberOfOpenCreditLinesAndLoans": open_lines,
            "NumberOfTimes90DaysLate": late_90,
            "NumberRealEstateLoansOrLines": re_loans,
            "NumberOfTime60-89DaysPastDueNotWorse": late_60,
            "NumberOfDependents": dep_out,
            "data_provenance": PROVENANCE,
        }
    )
    return df


def generate_loan_approval(n: int = N_LOAN, seed: int = RANDOM_STATE + 7) -> pd.DataFrame:
    """Model B/C — retail loan applications in LKR with CRIB scores.

    Approval is a noisy multi-factor process (CRIB, LTI, asset coverage, income,
    employment) — deliberately NOT a near-deterministic CRIB threshold.
    """
    rng = _rng(seed)
    # Annual income LKR: mid-2020s retail (anchored to HIES × inflation uplift)
    income_annum = np.clip(rng.lognormal(mean=13.9, sigma=0.55, size=n), 480_000, 12_000_000)
    crib = np.clip(rng.normal(620, 110, n).astype(int), 250, 900)

    education = rng.choice(["Graduate", "Not Graduate"], size=n, p=[0.48, 0.52])
    self_employed = rng.choice(["Yes", "No"], size=n, p=[0.28, 0.72])
    dependents = rng.choice([0, 1, 2, 3, 4], size=n, p=[0.25, 0.32, 0.25, 0.12, 0.06])
    loan_term = rng.choice([6, 12, 18, 24, 36, 48, 60], size=n, p=[0.08, 0.22, 0.18, 0.22, 0.15, 0.10, 0.05])

    # Requested loan: income-linked personal/housing mix (LKR)
    base_lti = rng.uniform(0.35, 2.8, n)
    loan_amount = np.clip(income_annum * base_lti * rng.uniform(0.85, 1.15, n), 100_000, 25_000_000)
    loan_amount = (loan_amount / 10_000).round() * 10_000

    residential = np.clip(income_annum * rng.uniform(0.5, 8.0, n), 0, 80_000_000)
    commercial = np.clip(income_annum * rng.uniform(0.0, 4.0, n) * (self_employed == "Yes"), 0, 50_000_000)
    luxury = np.clip(income_annum * rng.uniform(0.05, 1.5, n), 50_000, 15_000_000)
    bank = np.clip(income_annum * rng.uniform(0.1, 2.0, n), 0, 20_000_000)
    # Occasional negative residential (data error) like old Indian file — pipeline clips
    residential = np.where(rng.random(n) < 0.01, -rng.uniform(10_000, 200_000, n), residential)

    total_assets = np.maximum(residential, 0) + commercial + luxury + bank
    lti = loan_amount / np.maximum(income_annum, 1)
    coverage = total_assets / np.maximum(loan_amount, 1)

    # Multi-factor approval logit — CRIB matters but is not a hard rule
    z = (
        0.012 * (crib - 550)
        - 0.55 * np.clip(lti - 1.2, -1, 3)
        + 0.35 * np.clip(np.log1p(coverage), 0, 4)
        + 0.00000015 * income_annum
        + 0.15 * (education == "Graduate")
        - 0.12 * (self_employed == "Yes")
        - 0.08 * dependents
        + rng.normal(0, 1.05, n)
    )
    p_approve = 1 / (1 + np.exp(-z))
    approved = rng.random(n) < p_approve
    loan_status = np.where(approved, "Approved", "Rejected")

    df = pd.DataFrame(
        {
            "loan_id": np.arange(1, n + 1),
            "no_of_dependents": dependents,
            "education": education,
            "self_employed": self_employed,
            "income_annum": income_annum.round(0),
            "loan_amount": loan_amount.round(0),
            "loan_term": loan_term,
            "crib_score": crib,
            "residential_assets_value": residential.round(0),
            "commercial_assets_value": commercial.round(0),
            "luxury_assets_value": luxury.round(0),
            "bank_asset_value": bank.round(0),
            "loan_status": loan_status,
            "data_provenance": PROVENANCE,
        }
    )
    return df


def main() -> None:
    ensure_dirs()
    DATA_RAW.mkdir(parents=True, exist_ok=True)

    default_df = generate_default_risk()
    loan_df = generate_loan_approval()

    default_path = DATA_RAW / "credit_risk_lk_synthetic.csv"
    loan_path = DATA_RAW / "loan_approval_lk_synthetic.csv"
    default_df.to_csv(default_path, index=False)
    loan_df.to_csv(loan_path, index=False)

    # Also copy to repo root for notebooks that search ROOT
    from ml.config import ROOT

    default_df.drop(columns=["data_provenance"]).to_csv(ROOT / "credit_risk_lk_synthetic.csv", index=False)
    loan_df.drop(columns=["data_provenance"]).to_csv(ROOT / "loan_approval_lk_synthetic.csv", index=False)
    # Keep provenance column in data/raw only (or keep in both — keep in raw)
    # Root copies without provenance column for shape asserts that expect fixed cols;
    # actually Model A asserts 12 cols — provenance would break that. Root + raw without
    # extra col for training; provenance lives in sidecar JSON.

    # Rewrite without provenance column so shape matches pipeline expects
    default_train = default_df.drop(columns=["data_provenance"])
    loan_train = loan_df.drop(columns=["data_provenance"])
    default_train.to_csv(default_path, index=False)
    loan_train.to_csv(loan_path, index=False)
    default_train.to_csv(ROOT / "credit_risk_lk_synthetic.csv", index=False)
    loan_train.to_csv(ROOT / "loan_approval_lk_synthetic.csv", index=False)

    meta = {
        "synthetic": True,
        "never_real_applicant_records": True,
        "provenance": PROVENANCE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "model_a": {
                "path": str(default_path.as_posix()),
                "rows": len(default_train),
                "cols": list(default_train.columns),
                "default_rate": float(default_train["SeriousDlqin2yrs"].mean()),
                "currency": "LKR",
                "income_field": "MonthlyIncome",
            },
            "model_b_c": {
                "path": str(loan_path.as_posix()),
                "rows": len(loan_train),
                "cols": list(loan_train.columns),
                "approved_rate": float((loan_train["loan_status"] == "Approved").mean()),
                "currency": "LKR",
                "score_field": "crib_score",
                "score_range": [250, 900],
                "score_range_source": "CRIB Score Reference Guide / crib.lk FAQs",
                "approval_label_note": (
                    "loan_status is a noisy multi-factor function of CRIB, LTI, "
                    "asset coverage, income, education, employment — NOT a hard CRIB cutoff"
                ),
            },
        },
        "phase0": "reports/phase0_sri_lanka_research.md",
    }
    meta_path = DATA_RAW / "sri_lanka_synthetic.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (REPORTS_DIR / "sri_lanka_synthetic.meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    print(f"Wrote {default_path}  rows={len(default_train)}  default_rate={meta['files']['model_a']['default_rate']:.3f}")
    print(f"Wrote {loan_path}  rows={len(loan_train)}  approved_rate={meta['files']['model_b_c']['approved_rate']:.3f}")
    print(f"Wrote {meta_path}")
    print("SYNTHETIC — calibrated to Phase 0 sources; not real applicant records.")


if __name__ == "__main__":
    main()
