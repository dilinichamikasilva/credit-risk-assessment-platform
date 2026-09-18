"""API tests for Model B."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PAYLOAD = {
    "no_of_dependents": 2,
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 5000000,
    "loan_amount": 15000000,
    "loan_term": 240,
    "cibil_score": 750,
    "residential_assets_value": 10000000,
    "commercial_assets_value": 5000000,
    "luxury_assets_value": 2000000,
    "bank_asset_value": 3000000,
}


def test_model_b_loan_approval_endpoint():
    response = client.post("/predict/loan-approval", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"Approved", "Rejected"}
    assert body["approved"] == (body["status"] == "Approved")
    assert 0.0 <= body["approval_probability"] <= 1.0
    assert body["risk_tier"] in {"Poor", "Fair", "Good", "Excellent"}
    assert body["model_version"]


def test_model_b_rejects_missing_required_field():
    payload = dict(SAMPLE_PAYLOAD)
    del payload["cibil_score"]
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422


def test_model_b_rejects_invalid_cibil_score():
    payload = dict(SAMPLE_PAYLOAD)
    payload["cibil_score"] = 950
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422


def test_model_b_rejects_invalid_education():
    payload = dict(SAMPLE_PAYLOAD)
    payload["education"] = "graduate"  # wrong case - not a valid category
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422


def test_model_b_rejects_invalid_self_employed():
    payload = dict(SAMPLE_PAYLOAD)
    payload["self_employed"] = "Maybe"
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422
