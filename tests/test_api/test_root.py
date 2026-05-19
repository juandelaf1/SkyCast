from fastapi.testclient import TestClient
from app.main import app


class TestRootEndpoint:
    def test_root_returns_info(self):
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "SkyCast"
        assert "version" in data
        assert data["documentacion"] == "/docs"
        assert "endpoints" in data
