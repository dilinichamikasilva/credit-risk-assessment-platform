"""API tests for POST /predict/recommended-amount (Sasuni / Model C)."""
from __future__ import annotations

from app.models_db import Application, Assessment

SAMPLE_PAYLOAD = {
    "no_of_dependents": 2,
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 9_600_000,
    "loan_term": 12,
    "cibil_score": 778,
    "residential_assets_value": 2_400_000,
    "commercial_assets_value": 17_600_000,
    "luxury_assets_value": 22_700_000,
    "bank_asset_value": 8_000_000,
    "requested_amount": 20_000_000,
}


def test_recommended_amount_returns_sane_result(api_env):
    client, _ = api_env
    resp = client.post("/predict/recommended-amount", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommended_amount"] > 0
    assert body["predicted_amount"] > 0
    assert body["recommended_amount"] <= SAMPLE_PAYLOAD["requested_amount"]
    assert body["capped_at_requested"] == (
        body["recommended_amount"] < body["predicted_amount"]
    )
    assert body["model_version"]
    assert body["application_id"] is None


def test_recommended_amount_never_exceeds_requested(api_env):
    client, _ = api_env
    payload = {**SAMPLE_PAYLOAD, "requested_amount": 500_000}
    resp = client.post("/predict/recommended-amount", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommended_amount"] == 500_000
    assert body["capped_at_requested"] is True


def test_recommended_amount_rejects_bad_cibil(api_env):
    client, _ = api_env
    bad = {**SAMPLE_PAYLOAD, "cibil_score": 100}
    resp = client.post("/predict/recommended-amount", json=bad)
    assert resp.status_code == 422


def test_recommended_amount_persists_when_applicant_named(api_env):
    client, sessions = api_env
    payload = {**SAMPLE_PAYLOAD, "applicant_name": "Sasuni Demo"}
    resp = client.post("/predict/recommended-amount", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["application_id"] is not None

    with sessions() as db:
        app_row = db.get(Application, body["application_id"])
        assert app_row is not None
        assert app_row.applicant_name == "Sasuni Demo"
        assert app_row.status == "assessed"
        rows = db.query(Assessment).filter(Assessment.application_id == app_row.id).all()
        assert len(rows) == 1
        assert rows[0].model_key == "model_c"
