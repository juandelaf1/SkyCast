from fastapi.testclient import TestClient


class TestHealthAPI:
    HEALTH_URL = "/api/v1/health"
    STATS_URL = "/api/v1/health/stats"

    def test_health_no_auth_required(self):
        from app.main import app
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.get(self.HEALTH_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_health_tracks_requests(self, client: TestClient):
        client.get(self.HEALTH_URL)
        resp2 = client.get(self.HEALTH_URL)
        data = resp2.json()
        assert data["requests_total"] >= 2

    def test_stats_returns_data(self, client: TestClient):
        resp = client.get(self.STATS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "metricas_api" in data
        assert "datos" in data

    def test_stats_todays_records(self, client: TestClient):
        resp = client.get(self.STATS_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert "registros_hoy" in data["datos"]
        assert isinstance(data["datos"]["registros_hoy"], int)
