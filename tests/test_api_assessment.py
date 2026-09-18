"""API tests for POST /predict/full-assessment and GET /applications/{id} (Sasuni)."""
from __future__ import annotations

from app.models_db import Application, Assessment

FULL_PAYLOAD = {
    "applicant_name": "Flagship Demo",
    "revolving_utilization": 0.25,
    "age": 42,
    "times_30_59_days_late": 0,
    "debt_ratio": 0.28,
    "monthly_income": 150_000,
    "open_credit_lines": 5,
    "times_90_days_late": 0,
    "real_estate_loans": 1,
    "times_60_89_days_late": 0,
    "dependents": 2,
    "no_of_dependents": 2,
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 1_800_000,
    "loan_amount": 2_500_000,
    "loan_term": 36,
    "crib_score": 720,
    "residential_assets_value": 8_000_000,
    "commercial_assets_value": 0,
    "luxury_assets_value": 1_200_000,
    "bank_asset_value": 900_000,
}


def test_full_assessment_runs_all_three_and_saves(api_env):
    client, sessions = api_env
    resp = client.post("/predict/full-assessment", json=FULL_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()

    assert body["application_id"] > 0
    assert 0.0 <= body["default"]["probability"] <= 1.0
    assert body["default"]["risk_band"] in {"low", "medium", "high"}
    assert isinstance(body["approval"]["approved"], bool)
    assert 0.0 <= body["approval"]["approval_probability"] <= 1.0
    assert body["amount"]["recommended_amount"] <= FULL_PAYLOAD["loan_amount"]
    assert body["amount"]["recommended_amount"] > 0

    with sessions() as db:
        app_row = db.get(Application, body["application_id"])
        assert app_row is not None
        assert app_row.applicant_name == "Flagship Demo"
        assert app_row.status == "assessed"
        assert app_row.crib_score == 720
        keys = {
            row.model_key
            for row in db.query(Assessment).filter(Assessment.application_id == app_row.id)
        }
        assert keys == {"model_a", "model_b", "model_c"}


def test_full_assessment_requires_applicant_name(api_env):
    client, _ = api_env
    bad = dict(FULL_PAYLOAD)
    del bad["applicant_name"]
    resp = client.post("/predict/full-assessment", json=bad)
    assert resp.status_code == 422


def test_get_application_detail_includes_assessments(api_env):
    client, _ = api_env
    created = client.post("/predict/full-assessment", json=FULL_PAYLOAD)
    assert created.status_code == 200
    app_id = created.json()["application_id"]

    resp = client.get(f"/applications/{app_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == app_id
    assert body["applicant_name"] == "Flagship Demo"
    assert len(body["assessments"]) == 3
    assert {a["model_key"] for a in body["assessments"]} == {
        "model_a",
        "model_b",
        "model_c",
    }


def test_get_application_unknown_id_returns_404(api_env):
    client, _ = api_env
    resp = client.get("/applications/99999")
    assert resp.status_code == 404
