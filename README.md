# Credit Risk Assessment Platform (Sri Lanka)

AI credit and loan risk assessment: **three models**, one shared scikit-learn feature pipeline, FastAPI backend, and React frontend.

| | |
|---|---|
| Currency | **LKR** |
| Credit score field | **`crib_score`** (CRIB Score **250–900**, [CRIB](https://www.crib.lk)) |
| Model versions | `model_a_v2_lk`, `model_b_v2_lk`, `model_c_v2_lk` |

> **Indicative only.** Training data is **synthetic**, calibrated to published CRIB / DCS HIES anchors — **not** real applicant records. See [`reports/phase0_sri_lanka_research.md`](reports/phase0_sri_lanka_research.md).

---

## Quick start

```bash
python -m pip install -r requirements.txt

# API (terminal 1)
uvicorn app.main:app --reload
# → http://127.0.0.1:8000  ·  docs at /docs

# Frontend (terminal 2)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

In local Vite mode the frontend **proxies** `/predict`, `/applications`, `/analytics`, `/health`, and `/model-info` to `http://127.0.0.1:8000` (see `frontend/vite.config.js`). Leave `VITE_API_BASE_URL` unset unless the API is on another host.

On startup the API creates `data/app.db` and, if needed, renames an older `cibil_score` column to `crib_score` so History / Dashboard keep working after the Sri Lanka localization.

```bash
python -m pytest tests/ -q
```

---

## Models

| Model | Task | Artifact |
|---|---|---|
| **A** | Default / delinquency probability | `ml/models/model_a_default.pkl` |
| **B** | Loan approve / reject | `ml/models/model_b_approval.pkl` |
| **C** | Recommended loan amount (LKR) | `ml/models/model_c_amount.pkl` |

Shared transforms live in [`ml/pipeline/features.py`](ml/pipeline/features.py) — notebooks and the API must use the same module (do not fork cleaning in routers).

CRIB display tiers (Poor / Fair / Good / Excellent) are **project-defined bands** over 250–900 — not official CRIB letter grades.

---

## Data

| File | Used by | Notes |
|---|---|---|
| `data/raw/credit_risk_lk_synthetic.csv` | Model A | Synthetic; `MonthlyIncome` in LKR |
| `data/raw/loan_approval_lk_synthetic.csv` | Models B & C | Synthetic; amounts in LKR; `crib_score` |
| `german_credit_data.csv` | EDA only | No target label |

Regenerate:

```bash
python -m ml.training.generate_sri_lanka_dataset
python -m ml.training.prepare_data
```

Provenance: `data/raw/sri_lanka_synthetic.meta.json` (also under `reports/`).

---

## Train

```bash
python -m ml.training.train_default_model
python -m ml.training.train_approval_model
python -m ml.training.train_amount_model
```

Or run the notebooks under `ml/notebooks/` (they expect the LK CSVs and `crib_score`). Plots land in `reports/figures/`; metrics in `reports/metrics.json`.

---

## API & UI

- API overview: [`docs/api.md`](docs/api.md)
- Flagship flow: **New Risk Assessment** (`POST /predict/full-assessment`) runs A + B + C and saves the applicant
- Standalone tools: Default Risk, Loan Approval, Recommended Amount
- History / Application detail / Dashboard read from SQLite via `/applications` and `/analytics`

---

## Project layout (high level)

```
app/                 FastAPI routers, schemas, SQLite models
frontend/            React (Vite) UI
ml/pipeline/         Shared feature transformers
ml/training/         Dataset generator + train/prepare scripts
ml/models/           Trained .pkl + .meta.json
ml/notebooks/        EDA + training notebooks
data/raw/            Synthetic CSVs + provenance
reports/             Phase 0 research, metrics, figures
tests/               pytest
```
