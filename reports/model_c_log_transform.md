# Model C - log-transform decision (Member 4)

loan_amount is right-skewed (train skew=0.28). Raw-scale val MAE=2,623,932; log1p val MAE=2,603,139. Keep log1p. Requested amount is not a feature. recommended_amount = min(requested_amount, model_prediction) belongs in the API.
