# Credit Risk Assessment API

Sri Lanka localization: amounts in **LKR**, score field **`crib_score`** (CRIB **250–900**).
Models are trained on **synthetic** SL-calibrated data — indicative only.

Base URL (local dev): http://127.0.0.1:8000 — interactive docs at `/docs`
(full request/response schemas for every endpoint).
Run: `uvicorn app.main:app --reload`  |  Tests: `python -m pytest tests/ -q`

## Persistence model

- `applications` — one loan application (columns mirror `loan_approval_lk_synthetic.csv`).
  Predict routers create **thin** records (applicant name only) via
  `get_or_create_application()` and reuse them by name, so one applicant = one row.
- `assessments` — one row per model run; `inputs`/`outputs` are JSON so the same
  table stores Model A/B/C results. **Assessments are an immutable audit log —
  there is deliberately no PUT/DELETE for them** (leader spec 4.1). Corrections
  happen at the application identity level only.
- Deleting an application cascade-deletes every assessment linked to it.
- SQLite at `data/app.db`, created automatically on startup (never committed).

## Endpoints (implemented)

| Method | Path | Purpose | Success | Errors |
|---|---|---|---|---|
| GET | `/health` | Service + model availability | 200 | — |
| GET | `/model-info` | Version/task/metrics per loaded model | 200 | — |
| POST | `/predict/default-probability` | Model A: default probability + risk band | 200 | 422, 503 |
| POST | `/predict/recommended-amount` | Model C: recommended amount (capped at requested) | 200 | 422, 503 |
| POST | `/predict/full-assessment` | Flagship: run A+B+C together, always saved | 200 | 422, 503 |
| GET | `/applications/{id}` | One applicant's full record incl. every assessment | 200 | 404 |
| PUT | `/applications/{id}` | Identity/reference fix only (e.g. name typo) — assessment inputs are immutable | 200 | 404, 422 |
| DELETE | `/applications/{id}` | Delete applicant; cascade-deletes all their assessments | 204 | 404 |
| GET | `/analytics/summary` | Aggregates: volume, risk distribution, avg probability | 200 | — |

## Planned (not yet implemented — do not call)

| Method | Path | Purpose | Owner |
|---|---|---|---|
| POST | `/predict/loan-approval` | Model B; creates/links application, logs assessment | Sithumini |
| GET | `/applications` | List applicants, newest first, with assessment counts | Sithumini |

## Examples

### POST /predict/default-probability

Request:

```json
{
  "revolving_utilization": 0.25,
  "age": 42,
  "times_30_59_days_late": 0,
  "debt_ratio": 0.28,
  "monthly_income": 150000,
  "open_credit_lines": 5,
  "times_90_days_late": 0,
  "real_estate_loans": 1,
  "times_60_89_days_late": 0,
  "dependents": 2
}
```

Response (200):

```json
{
  "probability": 0.084,
  "risk_band": "low",
  "model_version": "model_a_v2_lk"
}
```

Missing/invalid fields → 422; model artifacts not trained/committed → 503.

### POST /predict/recommended-amount (Sasuni / Model C)

```json
{
  "no_of_dependents": 2,
  "education": "Graduate",
  "self_employed": "No",
  "income_annum": 2400000,
  "loan_term": 36,
  "crib_score": 720,
  "residential_assets_value": 9000000,
  "commercial_assets_value": 0,
  "luxury_assets_value": 1500000,
  "bank_asset_value": 1200000,
  "requested_amount": 3500000,
  "applicant_name": "Demo Applicant"
}
```

Response (200):

```json
{
  "recommended_amount": 3000000,
  "predicted_amount": 3003320,
  "capped_at_requested": false,
  "model_version": "model_c_v2_lk",
  "application_id": 1
}
```

`requested_amount` is **not** a model feature — it only drives
`recommended_amount = min(requested_amount, predicted_amount)`.
Omit `applicant_name` to skip persistence (`application_id` is then `null`).

### POST /predict/full-assessment (Sasuni / flagship)

Requires `applicant_name` and fields for Models A + B + C. Always creates (or
reuses) one application and logs three assessment rows. Response shape:

```json
{
  "application_id": 1,
  "default": { "probability": 0.08, "risk_band": "low", "model_version": "model_a_v2_lk" },
  "approval": { "approved": true, "approval_probability": 0.97, "model_version": "model_b_v2_lk" },
  "amount": {
    "recommended_amount": 20000000,
    "predicted_amount": 29266544,
    "capped_at_requested": true,
    "model_version": "model_c_v2_lk",
    "application_id": 1
  }
}
```

### GET /applications/1 (Sasuni)

Returns `ApplicationDetail` including the nested `assessments` list (inputs +
outputs for every model run). Unknown id → `404`.

### PUT /applications/1 — identity/reference corrections ONLY

```json
{ "applicant_name": "Ilma T. (corrected)" }
```

- → `200` full `ApplicationDetail`; the name changes, **everything else stays**.
- `{}` → `200`, nothing changes.
- Editing assessment inputs (`crib_score`, `loan_amount`, `status`, …) →
  `422` — the audit trail is immutable once assessments exist.
- Unknown id → `404`.

### DELETE /applications/1

- → `204` empty body; the application's assessment rows are removed by cascade.
- Repeat → `404 {"detail": "Application 1 not found"}`.
- UI note: confirm with the user before deleting (destructive).

### GET /analytics/summary

Response (200):

```json
{
  "total_applications": 2,
  "total_assessments": 3,
  "assessments_by_model": { "model_a": 2, "model_b": 1 },
  "assessments_by_risk_band": { "low": 1, "high": 1, "unknown": 1 },
  "applications_by_status": { "assessed": 1, "submitted": 1 },
  "avg_default_probability": 0.3
}
```

`risk_band` is `null` for models without a band (B/C) and is reported as
`"unknown"`. `avg_default_probability` is `null` until at least one Model A
run exists.

## Status codes

`200` OK · `204` Deleted · `404` Not found · `422` Validation (Pydantic `Field`
constraints, or non-identity field in PUT) · `503` Model artifacts not
trained/committed.

## Conventions

- One DB session per request via `Depends(get_db)`; tests override it with
  in-memory SQLite (see the `api_env` fixture in `tests/conftest.py`).
- Prediction logging contract (all predict routers):

```python
app_row = get_or_create_application(db, applicant_name=payload.applicant_name)
save_assessment(db, model_key=..., model_version=..., inputs=...,
                outputs=..., risk_band=..., application_id=app_row.id)
```

- `status` is system-managed (`submitted` → `assessed` by the predict flow);
  never user-editable via PUT.