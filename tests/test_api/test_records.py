from fastapi.testclient import TestClient


class TestRecordsAPI:
    URL = "/api/v1/registros"

    def test_get_records_empty(self, client: TestClient):
        resp = client.get(self.URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["pages"] == 1

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
        assert len(resp.json()["items"]) >= 1

    def test_get_records_limit(self, client: TestClient):
        for i in range(5):
            client.post(self.URL, json={
                "temperatura": float(20 + i), "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
                "estacion_id": 1,
            })
        resp = client.get(self.URL, params={"limit": 3})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 3
        assert data["total"] >= 5

    def test_get_records_pagination(self, client: TestClient):
        for i in range(5):
            client.post(self.URL, json={
                "temperatura": float(20 + i), "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
                "estacion_id": 1,
            })
        p1 = client.get(self.URL, params={"page": 1, "limit": 2}).json()
        assert len(p1["items"]) == 2
        assert p1["page"] == 1
        assert p1["pages"] == 3
        p2 = client.get(self.URL, params={"page": 2, "limit": 2}).json()
        assert len(p2["items"]) == 2
        assert p2["page"] == 2

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

    def test_create_record_geovalidacion_passes(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0,
            "humedad": 50.0,
            "viento": 10.0,
            "lluvia": 0.0,
            "estacion_id": 1,
            "lat": 40.4114,
            "lon": -3.6788,
        })
        assert resp.status_code == 200

    def test_create_record_geovalidacion_fails(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0,
            "humedad": 50.0,
            "viento": 10.0,
            "lluvia": 0.0,
            "estacion_id": 1,
            "lat": 28.0,
            "lon": -16.0,
        })
        assert resp.status_code == 400
        assert "Geovalidación" in resp.json()["detail"]

    def test_get_records_invalid_fecha_format(self, client: TestClient):
        resp = client.get(self.URL, params={"fecha": "not-a-date"})
        assert resp.status_code == 400
        assert "YYYY-MM-DD" in resp.json()["detail"]

    def test_create_record_invalid_fecha_format(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
            "estacion_id": 1, "fecha": "invalida",
        })
        assert resp.status_code == 400
        assert "YYYY-MM-DD" in str(resp.json()["detail"])

    def test_get_records_page_beyond_available(self, client: TestClient):
        resp = client.get(self.URL, params={"page": 999, "limit": 50})
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_get_records_invalid_page(self, client: TestClient):
        resp = client.get(self.URL, params={"page": 0})
        assert resp.status_code == 422

    def test_create_record_presion_out_of_range(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura": 22.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
            "estacion_id": 1, "presion": 2000.0,
        })
        assert resp.status_code == 422

    def test_get_records_filter_by_municipio(self, client: TestClient):
        client.post(self.URL, json={
            "temperatura": 22.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
            "estacion_id": 1,
        })
        resp = client.get(self.URL, params={"municipio": "Madrid"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1


class TestRecordsAPIAuth:
    URL = "/api/v1/registros"

    def test_get_records_no_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.get(self.URL)
        assert resp.status_code == 401

    def test_create_record_no_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.post(self.URL, json={
            "temperatura": 22.0, "humedad": 50.0, "viento": 10.0, "lluvia": 0.0,
            "estacion_id": 1,
        })
        assert resp.status_code == 401
