"""API tests for PUT/DELETE /applications/{id} - fresh in-memory DB per test."""
from app.models_db import Application, Assessment


def _seed(session_factory, **overrides) -> int:
    data = dict(
        applicant_name="Ilma Test", no_of_dependents=2, education="Graduate",
        self_employed="No", income_annum=9_600_000, loan_amount=29_900_000,
        loan_term=12, cibil_score=778, residential_assets_value=2_400_000,
        commercial_assets_value=17_600_000, luxury_assets_value=22_700_000,
        bank_asset_value=8_000_000,
    )
    data.update(overrides)
    with session_factory() as db:
        row = Application(**data)
        db.add(row)
        db.commit()
        return row.id


def test_put_updates_fields_and_returns_detail(api_env):
    client, sessions = api_env
    app_id = _seed(sessions)
    resp = client.put(f"/applications/{app_id}", json={"cibil_score": 700, "status": "assessed"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["cibil_score"] == 700
    assert body["status"] == "assessed"
    assert body["loan_amount"] == 29_900_000.0  # untouched field unchanged


def test_put_unknown_id_returns_404(api_env):
    client, _ = api_env
    resp = client.put("/applications/99999", json={"cibil_score": 700})
    assert resp.status_code == 404


def test_put_invalid_payload_returns_422(api_env):
    client, sessions = api_env
    app_id = _seed(sessions)
    resp = client.put(f"/applications/{app_id}", json={"cibil_score": 99999})
    assert resp.status_code == 422


def test_put_empty_body_changes_nothing(api_env):
    client, sessions = api_env
    app_id = _seed(sessions)
    resp = client.put(f"/applications/{app_id}", json={})
    assert resp.status_code == 200
    assert resp.json()["cibil_score"] == 778


def test_delete_removes_application_and_cascades(api_env):
    client, sessions = api_env
    app_id = _seed(sessions)
    with sessions() as db:
        db.add(Assessment(application_id=app_id, model_key="model_a",
                          model_version="model_a_v1", inputs={}, outputs={}))
        db.commit()

    resp = client.delete(f"/applications/{app_id}")
    assert resp.status_code == 204

    with sessions() as db:
        assert db.get(Application, app_id) is None
        assert db.query(Assessment).filter(Assessment.application_id == app_id).first() is None


def test_delete_unknown_id_returns_404(api_env):
    client, _ = api_env
    resp = client.delete("/applications/99999")
    assert resp.status_code == 404
