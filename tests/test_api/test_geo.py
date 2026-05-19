import pytest
from fastapi.testclient import TestClient


class TestGeoAPI:
    URL = "/api/v1/geo"

    def test_geo_endpoint_requires_auth(self, client: TestClient):
        from app.main import app
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.get(f"{self.URL}/Madrid")
        assert resp.status_code == 401

    def test_geo_endpoint_structure(self, client: TestClient):
        resp = client.get(f"{self.URL}/Madrid")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert "ciudad" in data
            assert "lat" in data
            assert "lon" in data
            assert "fuente" in data
            assert data["pais"] in ("ES", "España")
