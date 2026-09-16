from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "model_a" in body["models_loaded"]


def test_model_info_has_model_a():
    resp = client.get("/model-info")
    assert resp.status_code == 200
    body = resp.json()
    assert "model_a" in body["models"]
    assert body["models"]["model_a"]["task"] == "default_probability"
