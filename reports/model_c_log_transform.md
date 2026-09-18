# Model C — log-transform decision (Member 4)

synthetic, calibrated to CRIB Score 250-900 (crib.lk) and DCS HIES 2019 income anchors with mid-2020s LKR retail bands — NOT real applicant records. See reports/phase0_sri_lanka_research.md. Amounts are LKR. loan_amount is right-skewed (train skew=2.38). A raw-scale XGBRegressor had val MAE 771,206; the same booster with log1p/expm1 had val MAE 789,032. We keep the raw target. The requested amount is never a feature. recommended_amount = min(requested_amount, model_prediction) belongs in the API.
