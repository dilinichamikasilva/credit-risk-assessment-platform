from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SAMPLE_PAYLOAD = {
    "revolving_utilization": 0.3,
    "age": 45,
    "times_30_59_days_late": 0,
    "debt_ratio": 0.35,
    "monthly_income": 5000,
    "open_credit_lines": 6,
    "times_90_days_late": 0,
    "real_estate_loans": 1,
    "times_60_89_days_late": 0,
    "dependents": 2,
}


def test_predict_default_probability_returns_sane_result():
    resp = client.post("/predict/default-probability", json=SAMPLE_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["probability"] <= 1.0
    assert body["risk_band"] in {"low", "medium", "high"}
    assert body["model_version"]


def test_predict_default_probability_rejects_missing_field():
    bad_payload = dict(SAMPLE_PAYLOAD)
    del bad_payload["age"]
    resp = client.post("/predict/default-probability", json=bad_payload)
    assert resp.status_code == 422


def test_predict_default_probability_rejects_negative_income():
    bad_payload = dict(SAMPLE_PAYLOAD)
    bad_payload["monthly_income"] = -100
    resp = client.post("/predict/default-probability", json=bad_payload)
    assert resp.status_code == 422
