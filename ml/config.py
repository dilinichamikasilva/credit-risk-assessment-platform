from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "ml" / "models"
REPORTS_DIR = ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

RANDOM_STATE = 42
OPTUNA_TRIALS_DEFAULT = 20

DEFAULT_FILES = ("credit_risk_dataset.csv", "credit_risk_dataset_1.csv")
LOAN_FILE = "loan_approval_dataset.csv"
GERMAN_FILE = "german_credit_data.csv"

MODEL_A_VERSION = "model_a_v1"
MODEL_B_VERSION = "model_b_v1"
MODEL_C_VERSION = "model_c_v1"


def ensure_dirs() -> None:
    for path in (DATA_RAW, DATA_PROCESSED, MODELS_DIR, REPORTS_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)
