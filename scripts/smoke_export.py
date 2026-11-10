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


def main() -> int:
    # ensure m2m not required for smoke
    os.environ.pop("SKYCAST_M2M_REQUIRED", None)
    os.environ.pop("SKYCAST_M2M_KEYS", None)

    import app.api.v1.route_weather as rw
    import app.api.v1.validate as val
    from app.main import app

    # mock providers
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

    async def _none(*_a, **_k):
        return None

    rw._fetch_aemet_inventory = _empty_inventory
    rw._get_openmeteo_waypoint = _fake_wp
    val._buscar_estaciones_cercanas = _fake_stations
    val._get_openmeteo_temperature = _fake_temp
    val.aemet._fetch_station_data = _none

    with TestClient(app) as c:
        # health (contract capabilities)
        h = c.get("/api/v1/health")
        _write(OPS_DIR / "health.json", h.json())

        # route-weather contract
        route_payload = {
            "origen_lat": 40.4168,
            "origen_lon": -3.7038,
            "destino_lat": 41.3874,
            "destino_lon": 2.1686,
            "num_samples": 2,
        }
        r = c.post("/api/v1/route-weather", json=route_payload)
        _write(API_DIR / "route-weather.sample.json", r.json())

        # validate-observation contract
        val_payload = {
            "lat": 40.4168,
            "lon": -3.7038,
            "reporte": "helada intensa en la calzada",
            "temperatura_c": -2.0,
        }
        v = c.post("/api/v1/validate-observation", json=val_payload)
        _write(API_DIR / "validate-observation.sample.json", v.json())

        # readiness depends on DB; try and record outcome
        try:
            rd = c.get("/api/v1/health/ready")
            _write(OPS_DIR / "ready.json", rd.json())
        except Exception as e:
            _write(OPS_DIR / "ready.json", {"ready": None, "error": str(e)})

    print(f"Exported evidence to {API_DIR} and {OPS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
