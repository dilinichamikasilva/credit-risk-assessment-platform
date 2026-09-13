"""Member 4 — Model C: recommended loan amount.

Imports Member 1's shared pipeline only. Does not recode cleaning.
The API-layer cap (min(requested, predicted)) is documented, not trained.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import set_config
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor

from ml.config import (
    DATA_PROCESSED,
    DATA_RAW,
    FIGURES_DIR,
    MODEL_C_VERSION,
    MODELS_DIR,
    RANDOM_STATE,
    REPORTS_DIR,
    ROOT,
    ensure_dirs,
)
from ml.pipeline.features import LoanAmountFeatures, strip_loan_frame

CAT_COLS = ["education", "self_employed", "risk_tier"]
INFERENCE_RULE = "recommended_amount = min(requested_amount, model_prediction)"


def _find_loan_csv() -> Path:
    for path in (DATA_RAW / "loan_approval_dataset.csv", ROOT / "loan_approval_dataset.csv"):
        if path.exists():
            return path
    raise FileNotFoundError("loan_approval_dataset.csv not found")


def load_amount_split():
    """Use Member 1 processed C-splits when present; otherwise rebuild the same 70/15/15."""
    train_x = DATA_PROCESSED / "c_train.parquet"
    if train_x.exists():
        X_train = pd.read_parquet(train_x)
        X_val = pd.read_parquet(DATA_PROCESSED / "c_val.parquet")
        X_test = pd.read_parquet(DATA_PROCESSED / "c_test.parquet")
        y_train = pd.read_parquet(DATA_PROCESSED / "yc_train.parquet").iloc[:, 0].astype(float)
        y_val = pd.read_parquet(DATA_PROCESSED / "yc_val.parquet").iloc[:, 0].astype(float)
        y_test = pd.read_parquet(DATA_PROCESSED / "yc_test.parquet").iloc[:, 0].astype(float)
        source = "data/processed (Member 1)"
        return X_train, X_val, X_test, y_train, y_val, y_test, source

    loan_df = strip_loan_frame(pd.read_csv(_find_loan_csv()))
    work = loan_df[loan_df["loan_status"] == "Approved"].reset_index(drop=True)
    y = work["loan_amount"].astype(float)
    X = work.drop(columns=[c for c in ("loan_status", "loan_id", "loan_amount") if c in work.columns])
    strata = pd.qcut(y, q=5, duplicates="drop")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=strata, random_state=RANDOM_STATE
    )
    temp_strata = pd.qcut(y_temp, q=min(5, y_temp.nunique()), duplicates="drop")
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=temp_strata, random_state=RANDOM_STATE
    )
    return X_train, X_val, X_test, y_train, y_val, y_test, "rebuilt approved-only 70/15/15"


def _preprocessor(sample: pd.DataFrame) -> ColumnTransformer:
    cat = [c for c in CAT_COLS if c in sample.columns]
    num = [c for c in sample.columns if c not in cat]
    return ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat),
            ("num", "passthrough", num),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def _xgb() -> XGBRegressor:
    return XGBRegressor(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=4,
        tree_method="hist",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )


def make_pipeline(sample: pd.DataFrame, log_target: bool) -> Pipeline:
    model = _xgb()
    if log_target:
        model = TransformedTargetRegressor(
            regressor=model,
            func=np.log1p,
            inverse_func=np.expm1,
            check_inverse=False,
        )
    return Pipeline(
        [
            ("features", LoanAmountFeatures()),
            ("preprocess", _preprocessor(sample)),
            ("model", model),
        ]
    )


def regression_metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mape": float(np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1, None))) * 100),
    }


def main() -> None:
    set_config(transform_output="pandas")
    ensure_dirs()

    X_train, X_val, X_test, y_train, y_val, y_test, source = load_amount_split()
    if "loan_amount" in X_train.columns:
        raise ValueError("loan_amount leaked into features — Member 4 must drop the target from X")

    print(
        f"Model C split train/val/test={len(X_train)}/{len(X_val)}/{len(X_test)}  "
        f"source={source}  target_median={float(y_train.median()):,.0f}  "
        f"target_skew={float(y_train.skew()):.3f}"
    )

    preview = LoanAmountFeatures().fit(X_train).transform(X_train.head(5))
    assert "loan_amount" not in preview.columns
    assert "loan_to_income" not in preview.columns

    raw_pipe = make_pipeline(preview, log_target=False)
    log_pipe = make_pipeline(preview, log_target=True)
    raw_pipe.fit(X_train, y_train)
    log_pipe.fit(X_train, y_train)
    raw_val = regression_metrics(y_val, raw_pipe.predict(X_val))
    log_val = regression_metrics(y_val, log_pipe.predict(X_val))
    use_log = log_val["mae"] <= raw_val["mae"]
    print(f"Val MAE raw={raw_val['mae']:,.0f}  log1p={log_val['mae']:,.0f}  chosen={'log1p' if use_log else 'raw'}")

    pipe = log_pipe if use_log else raw_pipe
    val_metrics = log_val if use_log else raw_val
    test_pred = pipe.predict(X_test)
    test_metrics = regression_metrics(y_test, test_pred)
    print(
        f"Test MAE={test_metrics['mae']:,.0f}  RMSE={test_metrics['rmse']:,.0f}  "
        f"MAPE={test_metrics['mape']:.1f}%"
    )
    print(f"Downstream inference rule (API, not training): {INFERENCE_RULE}")

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(y_test, test_pred, alpha=0.25, s=12)
    lo = min(float(np.min(y_test)), float(np.min(test_pred)))
    hi = max(float(np.max(y_test)), float(np.max(test_pred)))
    ax.plot([lo, hi], [lo, hi], "--", color="gray")
    ax.set_xlabel("Actual loan amount")
    ax.set_ylabel("Predicted loan amount")
    ax.set_title("Model C — recommended loan amount")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "model_c_pred_vs_actual.png", dpi=140)
    plt.close(fig)

    try:
        import shap

        transformed = pipe.named_steps["preprocess"].transform(
            pipe.named_steps["features"].transform(X_test)
        )
        sample = transformed.sample(n=min(200, len(transformed)), random_state=1)
        inner = pipe.named_steps["model"]
        if hasattr(inner, "regressor_"):
            inner = inner.regressor_
        shap.summary_plot(shap.TreeExplainer(inner).shap_values(sample), sample, show=False, max_display=14)
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "shap_summary_model_c.png", dpi=140, bbox_inches="tight")
        plt.close()
        print(f"Saved {FIGURES_DIR / 'shap_summary_model_c.png'}")
    except Exception as exc:  # noqa: BLE001
        print(f"SHAP skipped: {exc}")

    log_note = (
        f"loan_amount is right-skewed (train skew={float(y_train.skew()):.2f}). "
        f"A raw-scale XGBRegressor had val MAE {raw_val['mae']:,.0f}; "
        f"the same booster with log1p/expm1 had val MAE {log_val['mae']:,.0f}. "
        f"We keep the {'log1p' if use_log else 'raw'} target. "
        f"The requested amount is never a feature. {INFERENCE_RULE} belongs in the API."
    )
    (REPORTS_DIR / "model_c_log_transform.md").write_text(
        "# Model C — log-transform decision (Member 4)\n\n" + log_note + "\n",
        encoding="utf-8",
    )

    metadata = {
        "model_version": MODEL_C_VERSION,
        "owner": "member_4",
        "task": "recommended_loan_amount",
        "target": "loan_amount (Approved applications only)",
        "pipeline": "ml.pipeline.features.LoanAmountFeatures",
        "target_transform": "log1p / expm1" if use_log else "none",
        "split_source": source,
        "split": {"train": len(X_train), "val": len(X_val), "test": len(X_test)},
        "metrics": {"val_raw": raw_val, "val_log1p": log_val, "val": val_metrics, "test": test_metrics},
        "inference_rule": INFERENCE_RULE,
        "notes": log_note,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    path = MODELS_DIR / "model_c_amount.pkl"
    joblib.dump(pipe, path)
    (MODELS_DIR / "model_c_amount.meta.json").write_text(
        json.dumps({**metadata, "artifact": str(path.as_posix())}, indent=2, default=str),
        encoding="utf-8",
    )

    metrics_path = REPORTS_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    metrics["model_c_amount"] = {
        "owner": "member_4",
        "metric": "MAE / RMSE (currency units)",
        "baseline_mae": raw_val["mae"],
        "tuned_mae": test_metrics["mae"],
        "tuned_rmse": test_metrics["rmse"],
        "tuned_mape": test_metrics["mape"],
        "target_transform": "log1p" if use_log else "raw",
        "trained_on": "approved_applications_only",
        "inference_rule": INFERENCE_RULE,
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")

    try:
        import mlflow

        mlflow.set_experiment("credit-risk-platform")
        with mlflow.start_run(run_name="model_c_xgb_regressor"):
            mlflow.log_param("owner", "member_4")
            mlflow.log_param("target_transform", "log1p" if use_log else "raw")
            mlflow.log_metric("val_mae_raw", raw_val["mae"])
            mlflow.log_metric("val_mae_log1p", log_val["mae"])
            mlflow.log_metric("test_mae", test_metrics["mae"])
            mlflow.log_metric("test_rmse", test_metrics["rmse"])
    except Exception as exc:  # noqa: BLE001
        print(f"MLflow skipped: {exc}")

    print(f"Saved {path}")


if __name__ == "__main__":
    main()
