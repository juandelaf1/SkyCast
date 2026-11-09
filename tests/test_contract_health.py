from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_has_contract():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["contract_version"] == "skycast-api/0.1"
    assert "capabilities" in body
    assert body["capabilities"].get("route_weather") is True


def test_health_echoes_correlation_id():
    r = client.get("/api/v1/health", headers={"X-Correlation-Id": "test-cid-123"})
    assert r.status_code == 200
    assert r.headers.get("X-Correlation-Id") == "test-cid-123"
