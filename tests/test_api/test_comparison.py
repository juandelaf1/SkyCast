import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestComparisonAPI:
    URL = "/api/v1/comparar"

    def test_comparison_no_aemet_data(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 22.0,
            "humedad_manual": 50.0,
            "viento_manual": 10.0,
            "lluvia_manual": 0.0,
            "municipio": "Madrid",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["municipio"] == "Madrid"
        assert data["fuente_aemet"] is None
        assert any("No hay datos AEMET" in a for a in data["alertas"])

    def test_comparison_within_thresholds(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 22.0,
            "humedad_manual": 50.0,
            "viento_manual": 10.0,
            "lluvia_manual": 0.0,
            "municipio": "Madrid",
        })
        data = resp.json()
        if data["fuente_aemet"]:
            for var, disc in data["discrepancias"].items():
                assert "umbral" in disc
                assert "diferencia" in disc

    def test_comparison_manual_only_data(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 30.0,
            "humedad_manual": 80.0,
            "viento_manual": 20.0,
            "lluvia_manual": 5.0,
            "municipio": "Getafe",
        })
        data = resp.json()
        assert data["fuente_manual"]["temperatura"] == 30.0
        assert data["fuente_manual"]["humedad"] == 80.0
        assert data["fuente_manual"]["viento"] == 20.0

    def test_comparison_invalid_date(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 22.0,
            "humedad_manual": 50.0,
            "viento_manual": 10.0,
            "lluvia_manual": 0.0,
            "municipio": "Madrid",
            "fecha": "fecha-invalida",
        })
        assert resp.status_code == 400

    def test_comparison_structure(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 25.0,
            "humedad_manual": 60.0,
            "viento_manual": 15.0,
            "lluvia_manual": 1.0,
            "municipio": "Madrid",
            "fecha": "2026-05-19",
        })
        data = resp.json()
        assert "municipio" in data
        assert "fecha" in data
        assert "fuente_aemet" in data
        assert "fuente_manual" in data
        assert "discrepancias" in data
        assert "alertas" in data

    def test_comparison_exact_threshold_temp(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 22.0, "humedad_manual": 50.0,
            "viento_manual": 10.0, "lluvia_manual": 0.0,
            "municipio": "Madrid",
        })
        data = resp.json()
        if "temperatura" in data.get("discrepancias", {}):
            assert data["discrepancias"]["temperatura"]["umbral"] == 3.0

    def test_comparison_threshold_exceeded_flag(self, client: TestClient):
        resp = client.post(self.URL, json={
            "temperatura_manual": 99.0, "humedad_manual": 99.0,
            "viento_manual": 99.0, "lluvia_manual": 99.0,
            "municipio": "Madrid",
        })
        data = resp.json()
        if data["fuente_aemet"]:
            for var, disc in data["discrepancias"].items():
                if disc["diferencia"] > disc["umbral"]:
                    assert disc["supera_umbral"] is True

    def test_comparison_with_aemet_data(self, client: TestClient, db_session):
        from app.db.models import Medicion, Estacion, FuenteDato
        from datetime import datetime
        est = db_session.query(Estacion).first()
        fuente = db_session.query(FuenteDato).filter(FuenteDato.codigo == "aemet").first()
        med = Medicion(estacion_id=est.id, fecha=datetime.now(), temperatura=22.0, humedad=50.0, viento=10.0, lluvia=0.0, fuente_id=fuente.id)
        db_session.add(med)
        db_session.commit()

        resp = client.post(self.URL, json={
            "temperatura_manual": 23.0, "humedad_manual": 52.0,
            "viento_manual": 12.0, "lluvia_manual": 1.0,
            "municipio": "Madrid",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["fuente_aemet"] is not None
        assert data["fuente_aemet"]["temperatura"] == 22.0
        assert "temperatura" in data["discrepancias"]

    def test_comparison_discrepancy_detected(self, client: TestClient, db_session):
        from app.db.models import Medicion, Estacion, FuenteDato
        from datetime import datetime
        est = db_session.query(Estacion).first()
        fuente = db_session.query(FuenteDato).filter(FuenteDato.codigo == "aemet").first()
        med = Medicion(estacion_id=est.id, fecha=datetime.now(), temperatura=20.0, humedad=50.0, viento=10.0, lluvia=0.0, fuente_id=fuente.id)
        db_session.add(med)
        db_session.commit()

        resp = client.post(self.URL, json={
            "temperatura_manual": 30.0, "humedad_manual": 50.0,
            "viento_manual": 10.0, "lluvia_manual": 0.0,
            "municipio": "Madrid",
        })
        data = resp.json()
        assert data["discrepancias"]["temperatura"]["supera_umbral"] is True
        assert data["discrepancias"]["temperatura"]["diferencia"] == 10.0
