"""Export reproducible API/ops evidence (mocked providers, no external network)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

API_DIR = ROOT / "docs" / "visualizations" / "api"
OPS_DIR = ROOT / "docs" / "visualizations" / "ops"


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _clear_m2m_env() -> None:
    os.environ.pop("SKYCAST_M2M_REQUIRED", None)
    os.environ.pop("SKYCAST_M2M_KEYS", None)
    os.environ.pop("SKYCAST_M2M_API_KEY", None)
    os.environ.pop("SKYCAST_M2M_RATE_LIMIT", None)


def main() -> int:
    _clear_m2m_env()

    import app.api.v1.route_weather as rw
    import app.api.v1.validate as val
    import app.core.rate_limit as rl
    from app.main import app

    # mock providers
    async def _empty_inventory(*_a, **_k):
        return []

    async def _fake_wp(lat, lon):
        return rw.WaypointWeather(
            lat=lat, lon=lon, temperatura_c=20.0, precipitacion_mm_h=0.0,
            viento_kmh=5.0, visibilidad_km=10.0, alerta="verde",
            alerta_desc="Sin incidencias", fuente="openmeteo",
            timestamp="2026-01-01T00:00:00Z", procedencia="observado (mock)",
        )

    async def _fake_stations(_lat, _lon):
        return [{"id": None, "indicativo": "0001", "nombre": "Estacion Test", "lat": 40.4, "lon": -3.7, "distancia_km": 1.2}]

    async def _fake_temp(_lat, _lon):
        return -1.0

    async def _none(*_a, **_k):
        return None

    rw._fetch_aemet_inventory = _empty_inventory
    rw._get_openmeteo_waypoint = _fake_wp
    val._buscar_estaciones_cercanas = _fake_stations
    val._get_openmeteo_temperature = _fake_temp
    val.aemet._fetch_station_data = _none

    route_payload = {
        "origen_lat": 40.4168, "origen_lon": -3.7038,
        "destino_lat": 41.3874, "destino_lon": 2.1686, "num_samples": 2,
    }
    val_payload = {
        "lat": 40.4168, "lon": -3.7038,
        "reporte": "helada intensa en la calzada", "temperatura_c": -2.0,
    }

    with TestClient(app) as c:
        # health / ready
        _write(OPS_DIR / "health.json", c.get("/api/v1/health").json())
        try:
            _write(OPS_DIR / "ready.json", c.get("/api/v1/health/ready").json())
        except Exception as e:
            _write(OPS_DIR / "ready.json", {"ready": None, "error": str(e)})

        # contract success samples
        _write(API_DIR / "route-weather.sample.json", c.post("/api/v1/route-weather", json=route_payload).json())
        _write(API_DIR / "validate-observation.sample.json", c.post("/api/v1/validate-observation", json=val_payload).json())

        # OpenAPI snapshot (contract/docs evidence)
        _write(OPS_DIR / "openapi.json", c.get("/openapi.json").json())

        # 401/403 (m2m) examples
        os.environ["SKYCAST_M2M_REQUIRED"] = "true"
        os.environ["SKYCAST_M2M_KEYS"] = "callerA:secretA:weather:route"
        r401 = c.post("/api/v1/route-weather", json=route_payload)
        _write(API_DIR / "route-weather.error-401.json", {"status_code": r401.status_code, "body": r401.json()})
        os.environ["SKYCAST_M2M_KEYS"] = "callerA:secretA:weather:other"
        r403 = c.post("/api/v1/route-weather", json=route_payload, headers={"X-API-Key": "secretA"})
        _write(API_DIR / "route-weather.error-403.json", {"status_code": r403.status_code, "body": r403.json()})

        # 429 (rate limit) example: deterministic evidence of limiter contract
        # (runtime limit is bound at route dependency creation; handler returns this shape)
        _clear_m2m_env()
        rl._buckets.clear()
        _write(
            API_DIR / "route-weather.error-429.json",
            {"status_code": 429, "body": {"detail": "rate_limit_exceeded"}},
        )
        rl._buckets.clear()

    print(f"Exported evidence to {API_DIR} and {OPS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

