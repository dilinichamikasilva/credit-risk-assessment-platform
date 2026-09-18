"""Train Model A (default probability) on Sri Lankan synthetic data.

SYNTHETIC DATA — see reports/phase0_sri_lanka_research.md and
data/raw/sri_lanka_synthetic.meta.json.

Usage:
  python -m ml.training.train_default_model
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.frozen import FrozenEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ml.config import (
    DATA_PROCESSED,
    DATA_PROVENANCE_NOTE,
    DATA_RAW,
    DEFAULT_FILES,
    FIGURES_DIR,
    MODEL_A_VERSION,
    MODELS_DIR,
    OPTUNA_TRIALS_DEFAULT,
    RANDOM_STATE,
    REPORTS_DIR,
    ROOT,
    ensure_dirs,
)
from ml.pipeline.features import DefaultRiskFeatures


def ks_statistic(y_true, y_score) -> float:
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    pos, neg = y_score[y_true == 1], y_score[y_true == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    return float(ks_2samp(pos, neg).statistic)


def classification_metrics(y_true, y_proba, threshold: float = 0.5) -> dict:
    y_pred = (np.asarray(y_proba) >= threshold).astype(int)
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    return {
        "auc_roc": float(roc_auc_score(y_true, y_proba)),
        "ks_statistic": ks_statistic(y_true, y_proba),
        "average_precision": float(average_precision_score(y_true, y_proba)),
        "brier": float(brier_score_loss(y_true, y_proba)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(report["1"]["precision"]),
        "recall": float(report["1"]["recall"]),
    }


def _find_default_csv():
    for name in DEFAULT_FILES:
        for path in (DATA_RAW / name, ROOT / name):
            if path.exists():
                return path
    raise FileNotFoundError(f"Default risk CSV not found; expected one of {DEFAULT_FILES}")


def load_split():
    train_x = DATA_PROCESSED / "a_train.parquet"
    if train_x.exists():
        X_train = pd.read_parquet(train_x)
        X_val = pd.read_parquet(DATA_PROCESSED / "a_val.parquet")
        X_test = pd.read_parquet(DATA_PROCESSED / "a_test.parquet")
        y_train = pd.read_parquet(DATA_PROCESSED / "ya_train.parquet").iloc[:, 0].astype(int)
        y_val = pd.read_parquet(DATA_PROCESSED / "ya_val.parquet").iloc[:, 0].astype(int)
        y_test = pd.read_parquet(DATA_PROCESSED / "ya_test.parquet").iloc[:, 0].astype(int)
        return X_train, X_val, X_test, y_train, y_val, y_test, "data/processed"

    path = _find_default_csv()
    df = pd.read_csv(path)
    y = df["SeriousDlqin2yrs"].astype(int)
    X = df.drop(columns=[c for c in ("SeriousDlqin2yrs", "Id") if c in df.columns])
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE
    )
    return X_train, X_val, X_test, y_train, y_val, y_test, str(path)


def main() -> None:
    ensure_dirs()
    X_train, X_val, X_test, y_train, y_val, y_test, source = load_split()
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    print(
        f"Model A train/val/test={len(X_train)}/{len(X_val)}/{len(X_test)}  "
        f"source={source}  default_rate={y_train.mean():.3f}  spw={scale_pos_weight:.2f}"
    )

    baseline = Pipeline(
        [
            ("features", DefaultRiskFeatures()),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced", max_iter=2000, random_state=RANDOM_STATE
                ),
            ),
        ]
    )
    baseline.fit(X_train, y_train)
    baseline_metrics = classification_metrics(y_test, baseline.predict_proba(X_test)[:, 1])
    print(
        f"Baseline  AUC={baseline_metrics['auc_roc']:.4f}  "
        f"KS={baseline_metrics['ks_statistic']:.4f}"
    )

    features = DefaultRiskFeatures().fit(X_train)
    X_train_f = features.transform(X_train)
    X_val_f = features.transform(X_val)
    X_test_f = features.transform(X_test)

    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 200, 500),
            "max_depth": trial.suggest_int("max_depth", 3, 7),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.15, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 12),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "gamma": trial.suggest_float("gamma", 1e-8, 1.0, log=True),
            "scale_pos_weight": scale_pos_weight,
            "max_delta_step": 1,
            "tree_method": "hist",
            "n_jobs": -1,
            "random_state": RANDOM_STATE,
            "eval_metric": "auc",
            "early_stopping_rounds": 40,
        }
        model = XGBClassifier(**params)
        model.fit(X_train_f, y_train, eval_set=[(X_val_f, y_val)], verbose=False)
        return float(roc_auc_score(y_val, model.predict_proba(X_val_f)[:, 1]))

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE)
    )
    study.optimize(objective, n_trials=OPTUNA_TRIALS_DEFAULT, show_progress_bar=False)
    best_params = study.best_params
    print(f"Best val AUC={study.best_value:.4f}")

    xgb = XGBClassifier(
        **best_params,
        scale_pos_weight=scale_pos_weight,
        max_delta_step=1,
        tree_method="hist",
        n_jobs=-1,
        random_state=RANDOM_STATE,
        eval_metric="auc",
        early_stopping_rounds=40,
    )
    xgb.fit(X_train_f, y_train, eval_set=[(X_val_f, y_val)], verbose=False)
    raw_test = classification_metrics(y_test, xgb.predict_proba(X_test_f)[:, 1])

    calibrated = CalibratedClassifierCV(
        estimator=FrozenEstimator(xgb), method="isotonic", cv=3
    )
    calibrated.fit(X_val_f, y_val)
    test_metrics = classification_metrics(y_test, calibrated.predict_proba(X_test_f)[:, 1])
    print(
        f"Calibrated AUC={test_metrics['auc_roc']:.4f}  "
        f"KS={test_metrics['ks_statistic']:.4f}  Brier={test_metrics['brier']:.4f}"
    )

    pipe = Pipeline([("features", features), ("model", calibrated)])
    proba_test = pipe.predict_proba(X_test)[:, 1]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fpr, tpr, _ = roc_curve(y_test, proba_test)
    axes[0].plot(fpr, tpr, label=f"AUC={roc_auc_score(y_test, proba_test):.3f}")
    axes[0].plot([0, 1], [0, 1], "--", color="gray")
    axes[0].set_title("ROC — Model A (LK synthetic)")
    axes[0].legend()
    frac, mean_pred = calibration_curve(y_test, proba_test, n_bins=10, strategy="quantile")
    axes[1].plot(mean_pred, frac, marker="o")
    axes[1].plot([0, 1], [0, 1], "--", color="gray")
    axes[1].set_title("Calibration — Model A")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "model_a_roc.png", dpi=140)
    fig.savefig(FIGURES_DIR / "model_a_calibration.png", dpi=140)
    plt.close(fig)

    metadata = {
        "model_version": MODEL_A_VERSION,
        "task": "default_probability",
        "target": "SeriousDlqin2yrs",
        "currency": "LKR",
        "data_provenance": DATA_PROVENANCE_NOTE,
        "notes": (
            f"{DATA_PROVENANCE_NOTE} "
            "MonthlyIncome is in LKR. Target is a multi-factor synthetic delinquency "
            "label (not a single hard rule)."
        ),
        "best_params": best_params,
        "scale_pos_weight": scale_pos_weight,
        "split_source": source,
        "metrics": {
            "baseline_auc": baseline_metrics["auc_roc"],
            "baseline_ks": baseline_metrics["ks_statistic"],
            "raw_auc": raw_test["auc_roc"],
            "tuned_auc": test_metrics["auc_roc"],
            "tuned_ks": test_metrics["ks_statistic"],
            "tuned_brier": test_metrics["brier"],
        },
        "risk_bands": {"low_lt": 0.1, "medium_lt": 0.35, "high_ge": 0.35},
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    path = MODELS_DIR / "model_a_default.pkl"
    joblib.dump(pipe, path)
    (MODELS_DIR / "model_a_default.meta.json").write_text(
        json.dumps({**metadata, "artifact": str(path.as_posix())}, indent=2, default=str),
        encoding="utf-8",
    )

    metrics_path = REPORTS_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    metrics["model_a_default"] = {
        "owner": "retrain_lk",
        "metric": "AUC-ROC / KS",
        "baseline_auc": baseline_metrics["auc_roc"],
        "tuned_auc": test_metrics["auc_roc"],
        "tuned_ks": test_metrics["ks_statistic"],
        "model_version": MODEL_A_VERSION,
        "data": "synthetic_lk",
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
