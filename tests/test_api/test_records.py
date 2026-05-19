from fastapi.testclient import TestClient


class TestRecordsAPI:
    URL = "/api/v1/registros"

    def test_get_records_empty(self, client: TestClient):
        resp = client.get(self.URL)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_record_success(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.5,
            "humedad": 60.0,
            "viento": 15.0,
            "lluvia": 0.0,
            "estacion_id": 1,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["temperatura"] == 22.5
        assert data["humedad"] == 60.0
        assert data["fuente"] == "manual"

    def test_create_record_invalid_temp(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 100.0,
            "humedad": 50.0,
            "viento": 10.0,
            "lluvia": 0.0,
            "estacion_id": 1,
        })
        assert resp.status_code == 422

    def test_create_record_validation_error(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0,
            "humedad": 200.0,
            "viento": -5.0,
            "lluvia": 0.0,
            "estacion_id": 1,
        })
        assert resp.status_code == 422

    def test_create_record_nonexistent_station(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0,
            "humedad": 50.0,
            "viento": 10.0,
            "lluvia": 0.0,
            "estacion_id": 999,
        })
        assert resp.status_code == 404

    def test_get_records_filter_by_fecha(self, client: TestClient):
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d")
        client.post(self.URL, json={
            "temperatura": 22.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
            "estacion_id": 1,
        })
        resp = client.get(self.URL, params={"fecha": fecha})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_get_records_limit(self, client: TestClient):
        for i in range(5):
            client.post(self.URL, json={
                "temperatura": float(20 + i), "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
                "estacion_id": 1,
            })
        resp = client.get(self.URL, params={"limit": 3})
        assert resp.status_code == 200
        assert len(resp.json()) <= 3

    def test_create_record_with_date(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 18.0,
            "humedad": 55.0,
            "viento": 12.0,
            "lluvia": 2.0,
            "estacion_id": 1,
            "fecha": "2026-05-01",
        })
        assert resp.status_code == 200
