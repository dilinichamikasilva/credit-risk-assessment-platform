"""Loads the trained model pipelines + their metadata once, and caches them.

Each entry in ml.config-relative ``MODELS_DIR`` is a joblib-dumped sklearn
Pipeline (features -> preprocessing -> model) plus a sibling ``.meta.json``
with version/metrics/feature info. Models are loaded lazily on first use and
cached for the lifetime of the process, so a model that a teammate hasn't
built yet (missing .pkl) doesn't block the whole app from starting.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import joblib

from app.config import MODEL_FILES, MODELS_DIR


class ModelNotAvailableError(RuntimeError):
    """Raised when a model's .pkl/.meta.json hasn't been trained/committed yet."""


@dataclass(frozen=True)
class LoadedModel:
    key: str
    name: str
    pipeline: Any
    meta: dict


def _load(key: str) -> LoadedModel:
    if key not in MODEL_FILES:
        raise ModelNotAvailableError(f"Unknown model key: {key}")
    name = MODEL_FILES[key]
    pkl_path = MODELS_DIR / f"{name}.pkl"
    meta_path = MODELS_DIR / f"{name}.meta.json"
    if not pkl_path.exists() or not meta_path.exists():
        raise ModelNotAvailableError(f"{key} ({name}) is not trained/committed yet")
    pipeline = joblib.load(pkl_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return LoadedModel(key=key, name=name, pipeline=pipeline, meta=meta)


@lru_cache(maxsize=None)
def get_model(key: str) -> LoadedModel:
    return _load(key)


def available_models() -> list[str]:
    """Model keys whose artifacts currently exist on disk (loaded or not)."""
    available = []
    for key, name in MODEL_FILES.items():
        pkl_path = MODELS_DIR / f"{name}.pkl"
        meta_path = MODELS_DIR / f"{name}.meta.json"
        if pkl_path.exists() and meta_path.exists():
            available.append(key)
    return available


def get_model_a() -> LoadedModel:
    return get_model("model_a")
