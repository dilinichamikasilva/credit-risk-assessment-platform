"""API tests for Model B."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Realistic mid-2020s LKR retail example (CRIB 250–900)
SAMPLE_PAYLOAD = {
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


def test_model_b_loan_approval_endpoint():
    response = client.post("/predict/loan-approval", json=SAMPLE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] in {"Approved", "Rejected"}
    assert body["approved"] == (body["status"] == "Approved")
    assert 0.0 <= body["approval_probability"] <= 1.0
    assert body["risk_tier"] in {"Poor", "Fair", "Good", "Excellent"}
    assert body["model_version"]
    assert "lk" in body["model_version"] or body["model_version"].startswith("model_b")


def test_model_b_rejects_missing_required_field():
    payload = dict(SAMPLE_PAYLOAD)
    del payload["crib_score"]
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422


def test_model_b_rejects_invalid_crib_score():
    payload = dict(SAMPLE_PAYLOAD)
    payload["crib_score"] = 950
    response = client.post("/predict/loan-approval", json=payload)
    assert response.status_code == 422


def test_model_b_rejects_crib_below_official_floor():
    payload = dict(SAMPLE_PAYLOAD)
    payload["crib_score"] = 200  # below official CRIB floor of 250
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
