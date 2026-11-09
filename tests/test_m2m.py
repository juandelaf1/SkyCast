"""Tests m2m (D5) para route-weather."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


PAYLOAD = {
    "origen_lat": 40.4168, "origen_lon": -3.7038,
    "destino_lat": 41.3874, "destino_lon": 2.1686,
    "num_samples": 2,
}


def test_route_weather_not_required_without_config(monkeypatch):
    import app.api.v1.route_weather as rw
    monkeypatch.delenv("SKYCAST_M2M_REQUIRED", raising=False)
    monkeypatch.delenv("SKYCAST_M2M_KEYS", raising=False)
    async def _fake_wp(lat, lon):
        return rw.WaypointWeather(lat=lat, lon=lon, temperatura_c=20.0, fuente="openmeteo", procedencia="observado (mock)")
    monkeypatch.setattr(rw, "_fetch_aemet_inventory", lambda *a, **k: _async_empty())
    monkeypatch.setattr(rw, "_get_openmeteo_waypoint", _fake_wp)
    r = client.post("/api/v1/route-weather", json=PAYLOAD)
    assert r.status_code == 200
    assert r.json()["contract_version"] == "skycast-route-weather/0.1"


async def _async_empty():
    return []


def test_route_weather_requires_m2m_when_configured(monkeypatch):
    monkeypatch.setenv("SKYCAST_M2M_REQUIRED", "true")
    monkeypatch.setenv("SKYCAST_M2M_KEYS", "poolar:secret-test-key:weather:route")
    r = client.post("/api/v1/route-weather", json=PAYLOAD)
    assert r.status_code == 401


def test_route_weather_rejects_wrong_scope(monkeypatch):
    monkeypatch.setenv("SKYCAST_M2M_REQUIRED", "true")
    monkeypatch.setenv("SKYCAST_M2M_KEYS", "poolar:secret-test-key:other:scope")
    r = client.post("/api/v1/route-weather", headers={"X-API-Key": "secret-test-key"}, json=PAYLOAD)
    assert r.status_code == 403
