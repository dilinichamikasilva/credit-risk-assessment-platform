"""API tests for GET /analytics/summary - fresh in-memory DB per test."""
from app.models_db import Application
from app.services.persistence import save_assessment


def _seed_once(session_factory) -> None:
    with session_factory() as db:
        a1 = Application(applicant_name="A", education="Graduate", self_employed="No",
                         income_annum=1_000_000, loan_amount=500_000, loan_term=10,
                         crib_score=800, status="assessed")
        a2 = Application(applicant_name="B", education="Not Graduate", self_employed="Yes",
                         income_annum=500_000, loan_amount=200_000, loan_term=5,
                         crib_score=500, status="submitted")
        db.add_all([a1, a2])
        db.commit()
        save_assessment(db, model_key="model_a", model_version="model_a_v1",
                        inputs={}, outputs={"probability": 0.10}, risk_band="low",
                        application_id=a1.id)
        save_assessment(db, model_key="model_a", model_version="model_a_v1",
                        inputs={}, outputs={"probability": 0.50}, risk_band="high",
                        application_id=a2.id)
        save_assessment(db, model_key="model_b", model_version="model_b_v1",
                        inputs={}, outputs={"approval": "Approved"}, risk_band=None,
                        application_id=a1.id)


def test_summary_counts(api_env):
    client, sessions = api_env
    _seed_once(sessions)
    resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_applications"] == 2
    assert body["total_assessments"] == 3
    assert body["assessments_by_model"] == {"model_a": 2, "model_b": 1}
    assert body["assessments_by_risk_band"] == {"low": 1, "high": 1, "unknown": 1}
    assert body["applications_by_status"] == {"assessed": 1, "submitted": 1}
    assert body["avg_default_probability"] == (0.10 + 0.50) / 2


def test_summary_empty_db(api_env):
    client, _ = api_env  # fresh, unseeded
    resp = client.get("/analytics/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_applications"] == 0
    assert body["total_assessments"] == 0
    assert body["avg_default_probability"] is None
