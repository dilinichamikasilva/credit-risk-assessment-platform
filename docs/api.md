# Credit Risk Assessment API

Base URL (local dev): http://127.0.0.1:8000 — interactive docs at `/docs`
(full request/response schemas for every endpoint).
Run: `uvicorn app.main:app --reload`  |  Tests: `python -m pytest tests/ -q`

## Persistence model

- `applications` — one loan application (columns mirror `loan_approval_dataset.csv`).
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
| PUT | `/applications/{id}` | Identity/reference fix only (e.g. name typo) — assessment inputs are immutable | 200 | 404, 422 |
| DELETE | `/applications/{id}` | Delete applicant; cascade-deletes all their assessments | 204 | 404 |
| GET | `/analytics/summary` | Aggregates: volume, risk distribution, avg probability | 200 | — |

## Planned (not yet implemented — do not call)

| Method | Path | Purpose | Owner |
|---|---|---|---|
| POST | `/predict/loan-approval` | Model B; creates/links application, logs assessment | Sithumini |
| POST | `/predict/recommended-amount` | Model C; creates/links application, logs assessment | Sasuni |
| POST | `/predict/full-assessment` | One application + all 3 assessments (A+B+C) in one call | Sasuni |
| GET | `/applications` | List applicants, newest first, with assessment counts | Sithumini |
| GET | `/applications/{id}` | One applicant's full record incl. every assessment | Sasuni |

## Examples

### POST /predict/default-probability

Request:

```json
{
  "revolving_utilization": 0.3,
  "age": 45,
  "times_30_59_days_late": 0,
  "debt_ratio": 0.35,
  "monthly_income": 5000,
  "open_credit_lines": 6,
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
  "model_version": "model_a_v1"
}
```

Missing/invalid fields → 422; model artifacts not trained/committed → 503.

### PUT /applications/1 — identity/reference corrections ONLY

```json
{ "applicant_name": "Ilma T. (corrected)" }
```

- → `200` full `ApplicationDetail`; the name changes, **everything else stays**.
- `{}` → `200`, nothing changes.
- Editing assessment inputs (`cibil_score`, `loan_amount`, `status`, …) →
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