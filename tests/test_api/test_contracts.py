"""Contract-focused tests for integration endpoints (no external network)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


ROUTE_PAYLOAD = {
    "origen_lat": 40.4168,
    "origen_lon": -3.7038,
    "destino_lat": 41.3874,
    "destino_lon": 2.1686,
    "num_samples": 2,
}

VALIDATE_PAYLOAD = {
    "lat": 40.4168,
    "lon": -3.7038,
    "reporte": "helada intensa en la calzada",
    "temperatura_c": -2.0,
}


def _clear_m2m(monkeypatch):
    monkeypatch.delenv("SKYCAST_M2M_REQUIRED", raising=False)
    monkeypatch.delenv("SKYCAST_M2M_KEYS", raising=False)
    monkeypatch.delenv("SKYCAST_M2M_API_KEY", raising=False)


def test_route_weather_contract_success(monkeypatch):
    import app.api.v1.route_weather as rw

    _clear_m2m(monkeypatch)

    async def _empty_inventory(*_a, **_k):
        return []

    async def _fake_wp(lat, lon):
        return rw.WaypointWeather(
            lat=lat,
            lon=lon,
            temperatura_c=20.0,
            precipitacion_mm_h=0.0,
            viento_kmh=5.0,
            visibilidad_km=10.0,
            alerta="verde",
            alerta_desc="Sin incidencias",
            fuente="openmeteo",
            timestamp="2026-01-01T00:00:00Z",
            procedencia="observado (mock)",
        )

    monkeypatch.setattr(rw, "_fetch_aemet_inventory", _empty_inventory)
    monkeypatch.setattr(rw, "_get_openmeteo_waypoint", _fake_wp)

    c = TestClient(app)
    r = c.post("/api/v1/route-weather", json=ROUTE_PAYLOAD)
    assert r.status_code == 200
    body = r.json()

    assert body["contract_version"] == "skycast-route-weather/0.1"
    assert isinstance(body["waypoints"], list) and len(body["waypoints"]) == 2
    for key in ("hazard_level", "duration_penalty_pct", "co2_penalty_pct", "summary", "fuente", "procedencia"):
        assert key in body
    # envelope/additive fields
    assert body.get("capability_id") == "climate.route_weather"
    assert body.get("status") == "ok"


def test_route_weather_validation_error():
    c = TestClient(app)
    # missing required fields
    r = c.post("/api/v1/route-weather", json={"origen_lat": 40.0})
    assert r.status_code == 422
    # out of range lat
    r2 = c.post(
        "/api/v1/route-weather",
        json={**ROUTE_PAYLOAD, "origen_lat": 999},
    )
    assert r2.status_code == 422


def test_validate_observation_contract_success(monkeypatch):
    import app.api.v1.validate as val

    _clear_m2m(monkeypatch)

    async def _fake_stations(_lat, _lon):
        return [
            {
                "id": None,
                "indicativo": "0001",
                "nombre": "Estacion Test",
                "lat": 40.4,
                "lon": -3.7,
                "distancia_km": 1.2,
            }
        ]

    async def _fake_temp(_lat, _lon):
        return -1.0

    monkeypatch.setattr(val, "_buscar_estaciones_cercanas", _fake_stations)
    monkeypatch.setattr(val, "_get_openmeteo_temperature", _fake_temp)
    # ensure AEMET path doesn't interfere
    monkeypatch.setattr(val.aemet, "_fetch_station_data", lambda *_a, **_k: _async_none())

    c = TestClient(app)
    r = c.post("/api/v1/validate-observation", json=VALIDATE_PAYLOAD)
    assert r.status_code == 200
    body = r.json()

    assert body["contract_version"] == "skycast-validate-observation/0.1"
    assert "valido" in body and isinstance(body["valido"], bool)
    assert "confianza" in body and 0 <= body["confianza"] <= 100
    assert isinstance(body["estaciones_cercanas"], list)
    for key in ("nota", "procedencia"):
        assert key in body
    assert body.get("capability_id") == "climate.validate_observation"
    assert body.get("status") in ("ok", "degraded")


async def _async_none():
    return None


def test_validate_observation_validation_error():
    c = TestClient(app)
    # missing required fields
    r = c.post("/api/v1/validate-observation", json={"lat": 40.0})
    assert r.status_code == 422
    r2 = c.post("/api/v1/validate-observation", json={**VALIDATE_PAYLOAD, "lat": 200})
    assert r2.status_code == 422


def test_health_ready_contract(client: TestClient):
    # /health capabilities/contract
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body.get("contract_version") == "skycast-api/0.1"
    caps = body.get("capabilities", {})
    assert caps.get("route_weather") is True
    assert caps.get("validate_observation") is True

    # /ready DB connectivity contract
    r2 = client.get("/api/v1/health/ready")
    assert r2.status_code == 200
    b2 = r2.json()
    assert b2.get("ready") is True
    assert b2.get("database") == "connected"
    assert b2.get("service") == "skycast-api"


def test_m2m_route_weather_errors_contract(monkeypatch):
    _clear_m2m(monkeypatch)
    monkeypatch.setenv("SKYCAST_M2M_REQUIRED", "true")
    monkeypatch.setenv("SKYCAST_M2M_KEYS", "callerA:secretA:weather:route")
    c = TestClient(app)

    # missing credentials
    r401 = c.post("/api/v1/route-weather", json=ROUTE_PAYLOAD)
    assert r401.status_code == 401

    # insufficient scope
    monkeypatch.setenv("SKYCAST_M2M_KEYS", "callerA:secretA:weather:other")
    r403 = c.post("/api/v1/route-weather", json=ROUTE_PAYLOAD, headers={"X-API-Key": "secretA"})
    assert r403.status_code == 403



