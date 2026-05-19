import pytest
from fastapi.testclient import TestClient


class TestAlertsAPI:
    URL = "/api/v1/alertas"

    def test_get_all_alerts(self, client: TestClient):
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 8
        variables = {a["variable"] for a in data}
        assert "temperatura" in variables
        assert "viento" in variables
        assert "lluvia" in variables
        assert "humedad" in variables

    def test_get_alerts_filter_by_variable(self, client: TestClient):
        resp = client.get(self.URL, params={"variable": "temperatura"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["variable"] == "temperatura" for a in data)

    def test_get_alerts_includes_niveles(self, client: TestClient):
        resp = client.get(self.URL, params={"variable": "viento"})
        data = resp.json()
        niveles = {a["nivel"] for a in data}
        assert "rojo" in niveles
        assert "naranja" in niveles

    def test_update_existing_alert(self, client: TestClient):
        resp = client.post(self.URL, json={
            "variable": "temperatura",
            "nivel": "rojo",
            "valor": 45.0,
            "descripcion": "Calor extremo actualizado",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_create_new_alert(self, client: TestClient):
        resp = client.post(self.URL, json={
            "variable": "temperatura",
            "nivel": "verde",
            "valor": 25.0,
            "descripcion": "Temperatura ideal",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["umbral"]["nivel"] == "verde"

    def test_alert_thresholds_values(self, client: TestClient):
        resp = client.get(self.URL)
        data = resp.json()
        umbrales = { (a["variable"], a["nivel"]): a["valor"] for a in data }
        assert umbrales[("temperatura", "rojo")] == 40.0
        assert umbrales[("temperatura", "naranja")] == 35.0
        assert umbrales[("viento", "rojo")] == 70.0
        assert umbrales[("humedad", "rojo")] == 90.0
