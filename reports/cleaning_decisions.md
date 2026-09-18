# Cleaning decisions

Logged while building the shared pipeline so training and the API stay aligned.

## credit_risk_lk_synthetic (Model A) — September 2026

- **SYNTHETIC** data calibrated to Phase 0 research (`reports/phase0_sri_lanka_research.md`).
  Never treat rows as real applicants. Provenance: `data/raw/sri_lanka_synthetic.meta.json`.
- **MonthlyIncome** is in **LKR** (mid-2020s nominal retail bands anchored to DCS HIES 2019).
- Missing income / dependents and late-payment sentinels (96/98) are handled the same way as
  the prior GMSC-style pipeline (`DefaultRiskFeatures`).
- **RevolvingUtilization** capped at 2.0; **DebtRatio** capped at 5.0; age &lt; 18 imputed.

## loan_approval_lk_synthetic (Models B and C)

- **SYNTHETIC** LKR amounts; score field is **`crib_score`** on the official CRIB range **250–900**
  (CRIB Score Reference Guide / crib.lk FAQs).
- Headers/categoricals may still need stripping — `strip_loan_frame` remains.
- **residential_assets_value** can be slightly negative (injected noise) — clipped at 0.
- **risk_tier** is derived from **project-defined** bins over 250–900
  (`RISK_TIER_BINS` in `ml/pipeline/features.py`) — **not** official CRIB letter grades.
- **Model C** trains on Approved rows only; `loan_amount` is never a Model C feature.
- **Model B labels** are a **noisy multi-factor** function (CRIB, LTI, asset coverage, income,
  education, employment) — deliberately **not** a near-deterministic CRIB cutoff
  (unlike the prior Indian public dataset).

## german_credit_data

- Auxiliary only (EDA). No model is trained on it for the Sri Lanka deployment.
