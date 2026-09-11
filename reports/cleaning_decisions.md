# Cleaning decisions

Logged while building the shared pipeline so training and the API stay aligned.

## credit_risk_dataset (Model A)

- **MonthlyIncome ~19.8% missing** — median impute inside `DefaultRiskFeatures.fit`. Median is robust to the long right tail; a missing flag was skipped to keep the first model simple.
- **NumberOfDependents ~2.6% missing** — fill with 0 (interpret as no dependents reported).
- **RevolvingUtilizationOfUnsecuredLines** max 50,708 — treat values above 2.0 as data errors and cap at 2.0.
- **DebtRatio** max 329,664 — GMSC stores a large integer when income is 0; cap at 5.0.
- **Late-payment columns 96/98** (269 rows) — Kaggle sentinel codes, replaced with the non-sentinel median learned at fit time.
- **age = 0** — invalid; impute the median adult age rather than clipping to 18.

## loan_approval_dataset (Models B and C)

- Headers and categorical values have leading spaces — strip immediately in `strip_loan_frame`.
- **residential_assets_value** can be negative — clip assets at 0.
- **risk_tier** is derived from CIBIL bins (Poor / Fair / Good / Excellent), not a trained grade model.
- **Model C** is trained on **Approved** rows only so the target is an amount the lender actually accepted. `loan_amount` is never a Model C feature (no leakage). A log1p target transform handles right skew. The `min(requested, predicted)` cap is applied at inference, not in training.
- **Model B near-perfect F1** is a dataset property, not a leak from the split: `loan_status` in this public file is almost a deterministic function of `cibil_score`. Keep CIBIL in the model (it is a legitimate application input) and discuss the separation in the report rather than chasing a lower score.

## german_credit_data

- This export has **no target / risk label**, so it is auxiliary only (EDA and feature ideas). No model is trained on it.
