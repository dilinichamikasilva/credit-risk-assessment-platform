"""Backend-app-level config, layered on top of ml.config."""
from __future__ import annotations

from ml.config import MODELS_DIR, RANDOM_STATE  # noqa: F401 - re-exported for app modules

APP_TITLE = "Credit Risk Assessment API"
APP_VERSION = "0.1.0"

# CORS: wide open for local dev; tighten before deploying.
CORS_ALLOW_ORIGINS = ["*"]

MODEL_FILES = {
    "model_a": "model_a_default",
    "model_b": "model_b_approval",
    "model_c": "model_c_amount",
}
