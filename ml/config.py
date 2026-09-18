from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "ml" / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RANDOM_STATE = 42
OPTUNA_TRIALS_DEFAULT = 12

# Sri Lankan synthetic CSVs (Phase 1). Legacy Indian/US filenames no longer used for training.
DEFAULT_FILES = ("credit_risk_lk_synthetic.csv",)
LOAN_FILE = "loan_approval_lk_synthetic.csv"
GERMAN_FILE = "german_credit_data.csv"  # auxiliary only; not used for SL retrain

MODEL_A_VERSION = "model_a_v2_lk"
MODEL_B_VERSION = "model_b_v2_lk"
MODEL_C_VERSION = "model_c_v2_lk"

DATA_PROVENANCE_NOTE = (
    "synthetic, calibrated to CRIB Score 250-900 (crib.lk) and DCS HIES 2019 income "
    "anchors with mid-2020s LKR retail bands — NOT real applicant records. "
    "See reports/phase0_sri_lanka_research.md."
)


def ensure_dirs() -> None:
    for path in (DATA_RAW, DATA_PROCESSED, MODELS_DIR, REPORTS_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)
