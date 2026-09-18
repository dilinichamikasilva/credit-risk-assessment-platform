"""Train Model B (loan approval) on Sri Lankan synthetic data.

SYNTHETIC DATA — see reports/phase0_sri_lanka_research.md.
Approval labels are multi-factor (not a near-deterministic CRIB cutoff).

Usage:
  python -m ml.training.train_approval_model
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn import set_config
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
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
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from ml.config import (
    DATA_PROCESSED,
    DATA_PROVENANCE_NOTE,
    DATA_RAW,
    FIGURES_DIR,
    LOAN_FILE,
    MODEL_B_VERSION,
    MODELS_DIR,
    RANDOM_STATE,
    REPORTS_DIR,
    ROOT,
    ensure_dirs,
)
from ml.pipeline.features import (
    CRIB_SCORE_MAX,
    CRIB_SCORE_MIN,
    RISK_TIER_BINS,
    RISK_TIER_LABELS,
    LoanApprovalFeatures,
    strip_loan_frame,
)

CAT_COLS = ["education", "self_employed", "risk_tier"]


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


def _find_loan_csv():
    for path in (DATA_RAW / LOAN_FILE, ROOT / LOAN_FILE):
        if path.exists():
            return path
    raise FileNotFoundError(f"{LOAN_FILE} not found")


def load_split():
    train_x = DATA_PROCESSED / "b_train.parquet"
    if train_x.exists():
        X_train = pd.read_parquet(train_x)
        X_val = pd.read_parquet(DATA_PROCESSED / "b_val.parquet")
        X_test = pd.read_parquet(DATA_PROCESSED / "b_test.parquet")
        y_train = pd.read_parquet(DATA_PROCESSED / "yb_train.parquet").iloc[:, 0].astype(int)
        y_val = pd.read_parquet(DATA_PROCESSED / "yb_val.parquet").iloc[:, 0].astype(int)
        y_test = pd.read_parquet(DATA_PROCESSED / "yb_test.parquet").iloc[:, 0].astype(int)
        return X_train, X_val, X_test, y_train, y_val, y_test, "data/processed"

    loan_df = strip_loan_frame(pd.read_csv(_find_loan_csv()))
    y = (loan_df["loan_status"] == "Approved").astype(int)
    X = loan_df.drop(columns=[c for c in ("loan_status", "loan_id") if c in loan_df.columns])
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE
    )
    return X_train, X_val, X_test, y_train, y_val, y_test, str(_find_loan_csv())


def make_preprocessor(sample: pd.DataFrame) -> ColumnTransformer:
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


def main() -> None:
    set_config(transform_output="pandas")
    ensure_dirs()
    X_train, X_val, X_test, y_train, y_val, y_test, source = load_split()
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    print(
        f"Model B train/val/test={len(X_train)}/{len(X_val)}/{len(X_test)}  "
        f"source={source}  approved_rate={y_train.mean():.3f}"
    )
    assert "crib_score" in X_train.columns, "expected crib_score column after SL rename"

    preview = LoanApprovalFeatures().fit(X_train).transform(X_train.head(5))
    rf_pipe = Pipeline(
        [
            ("features", LoanApprovalFeatures()),
            ("preprocess", make_preprocessor(preview)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    min_samples_leaf=2,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                ),
            ),
        ]
    )
    xgb_pipe = Pipeline(
        [
            ("features", LoanApprovalFeatures()),
            ("preprocess", make_preprocessor(preview)),
            (
                "model",
                XGBClassifier(
                    n_estimators=400,
                    max_depth=5,
                    learning_rate=0.05,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    scale_pos_weight=scale_pos_weight,
                    tree_method="hist",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                    eval_metric="logloss",
                ),
            ),
        ]
    )
    rf_pipe.fit(X_train, y_train)
    xgb_pipe.fit(X_train, y_train)
    rf_val = classification_metrics(y_val, rf_pipe.predict_proba(X_val)[:, 1])
    xgb_val = classification_metrics(y_val, xgb_pipe.predict_proba(X_val)[:, 1])
    print(f"RandomForest val F1={rf_val['f1']:.4f} AUC={rf_val['auc_roc']:.4f}")
    print(f"XGBoost       val F1={xgb_val['f1']:.4f} AUC={xgb_val['auc_roc']:.4f}")

    winner_name, pipe = (
        ("random_forest", rf_pipe) if rf_val["f1"] >= xgb_val["f1"] else ("xgboost", xgb_pipe)
    )
    test_metrics = classification_metrics(y_test, pipe.predict_proba(X_test)[:, 1])
    print(
        f"Winner={winner_name}  test F1={test_metrics['f1']:.4f}  "
        f"AUC={test_metrics['auc_roc']:.4f}"
    )

    # Soft check: should not be near-perfect like the old Indian CIBIL-rule dataset
    if test_metrics["f1"] > 0.995 and test_metrics["auc_roc"] > 0.999:
        print(
            "WARNING: near-perfect metrics — label may still be too score-dominated; "
            "review generator noise."
        )

    proba = pipe.predict_proba(X_test)[:, 1]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    fpr, tpr, _ = roc_curve(y_test, proba)
    ax.plot(fpr, tpr, label=f"AUC={roc_auc_score(y_test, proba):.3f}")
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set_title("ROC — Model B (LK synthetic)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "model_b_roc.png", dpi=140)
    plt.close(fig)

    notes = (
        f"{DATA_PROVENANCE_NOTE} "
        f"CRIB score range {CRIB_SCORE_MIN}-{CRIB_SCORE_MAX} (crib.lk Score Reference Guide). "
        f"Project risk_tier bins={RISK_TIER_BINS} labels={RISK_TIER_LABELS} "
        "(NOT official CRIB letter grades). "
        "loan_status is a noisy multi-factor label (CRIB, LTI, asset coverage, income, "
        "education, employment) — deliberately NOT a near-deterministic CRIB cutoff "
        "(unlike the prior Indian public dataset)."
    )
    metadata = {
        "model_version": MODEL_B_VERSION,
        "task": "loan_approval",
        "winner": winner_name,
        "currency": "LKR",
        "score_field": "crib_score",
        "score_range": [CRIB_SCORE_MIN, CRIB_SCORE_MAX],
        "score_range_source": "CRIB Score Reference Guide / crib.lk FAQs",
        "risk_tier_bins": RISK_TIER_BINS,
        "risk_tier_labels": RISK_TIER_LABELS,
        "risk_tier_note": "Project-defined bands over official 250-900 CRIB range; not official CRIB grades.",
        "data_provenance": DATA_PROVENANCE_NOTE,
        "metrics": {
            "val_rf_f1": rf_val["f1"],
            "val_xgb_f1": xgb_val["f1"],
            "test_f1": test_metrics["f1"],
            "test_auc": test_metrics["auc_roc"],
        },
        "notes": notes,
        "split_source": source,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    path = MODELS_DIR / "model_b_approval.pkl"
    joblib.dump(pipe, path)
    (MODELS_DIR / "model_b_approval.meta.json").write_text(
        json.dumps({**metadata, "artifact": str(path.as_posix())}, indent=2, default=str),
        encoding="utf-8",
    )

    metrics_path = REPORTS_DIR / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    metrics["model_b_approval"] = {
        "owner": "retrain_lk",
        "metric": "F1 / AUC",
        "test_f1": test_metrics["f1"],
        "test_auc": test_metrics["auc_roc"],
        "winner": winner_name,
        "model_version": MODEL_B_VERSION,
        "data": "synthetic_lk",
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
