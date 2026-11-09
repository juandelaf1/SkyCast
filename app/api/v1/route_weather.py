import json
import logging
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.audit import audit_integration
from app.core.m2m import require_m2m_if_configured
from app.core.rate_limit import rate_limit
from app.core.utils import haversine, parse_aemet_coordinate
from app.services.aemet_service import AemetService

router = APIRouter()
logger = logging.getLogger(__name__)

# URL base de Open-Meteo (sin API key)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# Número máximo de waypoints por consulta
MAX_SAMPLES = 10
STATION_RADIUS_KM = 50.0


class RouteWeatherRequest(BaseModel):
    origen_lat: float = Field(..., ge=-90, le=90, description="Latitud de origen")
    origen_lon: float = Field(..., ge=-180, le=180, description="Longitud de origen")
    destino_lat: float = Field(..., ge=-90, le=90, description="Latitud de destino")
    destino_lon: float = Field(..., ge=-180, le=180, description="Longitud de destino")
    num_samples: int = Field(5, ge=1, le=MAX_SAMPLES, description="Numero de waypoints a muestrear")

    class Config:
        extra = "allow"


class WaypointWeather(BaseModel):
    lat: float
    lon: float
    temperatura_c: Optional[float] = None
    precipitacion_mm_h: Optional[float] = None
    viento_kmh: Optional[float] = None
    visibilidad_km: Optional[float] = None
    alerta: str = "verde"
    alerta_desc: str = ""
    fuente: str = "desconocida"
    timestamp: Optional[str] = None
    procedencia: str = "observado (fuente meteorologica) o estimado segun fuente"


class RouteWeatherResponse(BaseModel):
    contract_version: str = "skycast-route-weather/0.1"
    waypoints: list[WaypointWeather]
    hazard_level: str = "verde"
    duration_penalty_pct: float = 0.0
    co2_penalty_pct: float = 0.0
    summary: str = ""
    fuente: str = "desconocida"
    procedencia: str = "observado (aemet/open-meteo por waypoint) + estimado (agregacion/penalizacion)"
    # Additive ecosystem envelope fields (backward-compatible)
    capability_id: Optional[str] = "climate.route_weather"
    correlation_id: Optional[str] = None
    status: Optional[str] = "ok"
    data_status: Optional[str] = "estimated"
    provenance: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    warnings: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None

    class Config:
        extra = "allow"


def _classify_alert(temp: Optional[float], precip: Optional[float], wind: Optional[float]) -> tuple[str, str]:
    """Devuelve (nivel_alerta, descripcion) basado en condiciones meteorológicas."""
    niveles = {"verde": 0, "amarillo": 1, "naranja": 2, "rojo": 3}
    max_nivel = 0
    desc = []

    if temp is not None:
        if temp <= 0:
            max_nivel = max(max_nivel, niveles["naranja"])
            desc.append(f"T <= 0°C ({temp}°C)")
        elif temp >= 40:
            max_nivel = max(max_nivel, niveles["rojo"])
            desc.append(f"Calor extremo ({temp}°C)")
        elif temp >= 35:
            max_nivel = max(max_nivel, niveles["naranja"])
            desc.append(f"Calor alto ({temp}°C)")
        elif temp >= 30:
            max_nivel = max(max_nivel, niveles["amarillo"])
            desc.append(f"Calor moderado ({temp}°C)")

    if precip is not None:
        if precip >= 30:
            max_nivel = max(max_nivel, niveles["rojo"])
            desc.append(f"Lluvia intensa ({precip} mm/h)")
        elif precip >= 15:
            max_nivel = max(max_nivel, niveles["naranja"])
            desc.append(f"Lluvia moderada ({precip} mm/h)")
        elif precip > 2:
            max_nivel = max(max_nivel, niveles["amarillo"])
            desc.append(f"Lluvia ({precip} mm/h)")

    if wind is not None:
        if wind >= 70:
            max_nivel = max(max_nivel, niveles["rojo"])
            desc.append(f"Viento muy fuerte ({wind} km/h)")
        elif wind >= 50:
            max_nivel = max(max_nivel, niveles["naranja"])
            desc.append(f"Viento fuerte ({wind} km/h)")
        elif wind > 40:
            max_nivel = max(max_nivel, niveles["amarillo"])
            desc.append(f"Viento ({wind} km/h)")

    nombres = {0: "verde", 1: "amarillo", 2: "naranja", 3: "rojo"}
    return nombres[max_nivel], "; ".join(desc) if desc else "Sin incidencias"


def _aggregate_route(waypoints: list[WaypointWeather]) -> RouteWeatherResponse:
    """Agrega waypoints individuales en una evaluacion de ruta completa."""
    if not waypoints:
        return RouteWeatherResponse()

    niveles = {"verde": 0, "amarillo": 1, "naranja": 2, "rojo": 3}
    nombres = {0: "verde", 1: "amarillo", 2: "naranja", 3: "rojo"}
    max_nivel = 0
    rain_count = 0
    wind_count = 0

    for wp in waypoints:
        lvl = niveles.get(wp.alerta, 0)
        if lvl > max_nivel:
            max_nivel = lvl
        if wp.precipitacion_mm_h and wp.precipitacion_mm_h > 2:
            rain_count += 1
        if wp.viento_kmh and wp.viento_kmh > 40:
            wind_count += 1

    duration_penalty = 0.0
    if rain_count > len(waypoints) // 2:
        duration_penalty += 15
    if wind_count > len(waypoints) // 2:
        duration_penalty += 10
    if max_nivel >= 2:  # naranja o peor
        duration_penalty += 25

    alerts = []
    if max_nivel >= 1:
        alerts.append(nombres[max_nivel])
    if rain_count > 0:
        alerts.append(f"lluvia en {rain_count}/{len(waypoints)} puntos")
    if wind_count > 0:
        alerts.append(f"viento fuerte en {wind_count}/{len(waypoints)} puntos")

    fuentes = set(wp.fuente for wp in waypoints if wp.fuente != "desconocida")
    fuente_txt = ", ".join(fuentes) if fuentes else "openmeteo"

    return RouteWeatherResponse(
        waypoints=waypoints,
        hazard_level=nombres[max_nivel],
        duration_penalty_pct=duration_penalty,
        co2_penalty_pct=round(duration_penalty * 0.7, 1),
        summary=" | ".join(alerts) if alerts else "Sin incidencias",
        fuente=fuente_txt,
    )


async def _get_openmeteo_waypoint(lat: float, lon: float) -> Optional[WaypointWeather]:
    """Obtiene clima actual para un punto usando Open-Meteo."""
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            OPEN_METEO_BASE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,precipitation,wind_speed_10m,visibility",
                "timezone": "auto",
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        current = data.get("current", {})

        temp = current.get("temperature_2m")
        precip = current.get("precipitation", 0)
        wind = current.get("wind_speed_10m")
        visibility_m = current.get("visibility")

        alerta, alerta_desc = _classify_alert(temp, precip, wind)

        return WaypointWeather(
            lat=round(lat, 6),
            lon=round(lon, 6),
            temperatura_c=temp,
            precipitacion_mm_h=precip,
            viento_kmh=wind,
            visibilidad_km=round(visibility_m / 1000, 1) if visibility_m else None,
            alerta=alerta,
            alerta_desc=alerta_desc,
            fuente="openmeteo",
            timestamp=current.get("time"),
            procedencia="observado (open-meteo)",
        )


async def _fetch_aemet_inventory(aemet: AemetService) -> list[dict]:
    if not aemet.api_key:
        return []
    import httpx
    try:
        url = f"{aemet.base_url}/valores/climatologicos/inventarioestaciones/todasestaciones"
        headers = {"api_key": aemet.api_key}
        async with httpx.AsyncClient(timeout=aemet.timeout) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json()
            if isinstance(data, dict):
                datos_url = data.get("datos")
                if not datos_url:
                    return []
                resp2 = await client.get(datos_url)
                if resp2.status_code != 200:
                    return []
                estaciones = json.loads(resp2.content.decode("ISO-8859-15"))
            else:
                estaciones = data
        return estaciones if isinstance(estaciones, list) else []
    except Exception as e:
        logger.warning(f"No se pudo obtener inventario AEMET para ruta: {e}")
        return []


def _nearest_station(lat: float, lon: float, inventory: list[dict]) -> Optional[dict]:
    nearest = None
    min_dist = float("inf")
    for est in inventory:
        try:
            est_lat = parse_aemet_coordinate(est.get("latitud"))
            est_lon = parse_aemet_coordinate(est.get("longitud"))
            if est_lat is None or est_lon is None:
                continue
            dist = haversine(lat, lon, est_lat, est_lon)
            if dist < min_dist:
                min_dist = dist
                nearest = {"indicativo": est.get("indicativo", ""), "distancia_km": dist}
        except (ValueError, TypeError):
            continue
    if nearest and nearest["distancia_km"] <= STATION_RADIUS_KM:
        return nearest
    return None


async def _get_aemet_waypoint(lat: float, lon: float, aemet: AemetService, inventory: list[dict]) -> Optional[WaypointWeather]:
    station = _nearest_station(lat, lon, inventory)
    if not station or not station.get("indicativo"):
        return None
    datos = await aemet._fetch_station_data(station["indicativo"])
    if not datos or datos.get("temperatura") is None:
        return None
    temp = datos.get("temperatura")
    precip = datos.get("lluvia")
    wind = datos.get("viento")
    alerta, alerta_desc = _classify_alert(temp, precip, wind)
    return WaypointWeather(
        lat=round(lat, 6),
        lon=round(lon, 6),
        temperatura_c=temp,
        precipitacion_mm_h=precip if precip is not None else 0.0,
        viento_kmh=wind,
        visibilidad_km=None,
        alerta=alerta,
        alerta_desc=alerta_desc,
        fuente="aemet",
        timestamp=datetime.utcnow().isoformat(),
        procedencia="observado (aemet, estacion cercana)",
    )


def _parse_route_request(body: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(body, dict) and body.get("capability_id") == "climate.route_weather" and isinstance(body.get("payload"), dict):
        return body["payload"]
    return body if isinstance(body, dict) else {}


@router.post("/route-weather", response_model=RouteWeatherResponse, tags=["Clima por ruta"])
async def route_weather(
    request: Request,
    _m2m: object = Depends(require_m2m_if_configured("weather:route")),
    _rl: None = Depends(rate_limit("SKYCAST_M2M_RATE_LIMIT", "120/minute")),
):
    """
    Obtiene condiciones meteorológicas a lo largo de una ruta.

    Interpola waypoints entre origen y destino y consulta el clima
    en cada uno. Útil para EnRuta: permite saber si una ruta de transporte
    atraviesa zonas con riesgo meteorológico antes de aceptar el matching.
    En España, prefiere AEMET cuando hay clave configurada; si no, usa Open-Meteo.
    Acepta body legacy o envelope ecosystem (payload).
    """
    raw = await request.json()
    body = _parse_route_request(raw)
    req = RouteWeatherRequest(**body)
    correlation_id = (raw.get("correlation_id") if isinstance(raw, dict) else None) or getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id") or str(uuid4())

    lat1, lon1 = req.origen_lat, req.origen_lon
    lat2, lon2 = req.destino_lat, req.destino_lon
    num_samples = min(req.num_samples, MAX_SAMPLES)

    aemet = AemetService()
    inventory = []
    aemet_preferred = bool(aemet.api_key and all(AemetService._is_spain(lat, lon) for lat, lon in [(lat1, lon1), (lat2, lon2)]))
    if aemet_preferred:
        inventory = await _fetch_aemet_inventory(aemet)

    waypoints = []
    aemet_used = 0
    for i in range(num_samples):
        frac = i / (num_samples - 1) if num_samples > 1 else 0
        lat = lat1 + (lat2 - lat1) * frac
        lon = lon1 + (lon2 - lon1) * frac

        wp = None
        if inventory and AemetService._is_spain(lat, lon):
            try:
                wp = await _get_aemet_waypoint(lat, lon, aemet, inventory)
            except Exception as e:
                logger.warning(f"AEMET waypoint fallo ({lat},{lon}): {e}")
        if wp is None:
            wp = await _get_openmeteo_waypoint(lat, lon)
        elif wp.fuente == "aemet":
            aemet_used += 1
        if wp:
            if getattr(wp, "fuente", None) == "aemet":
                pass
            waypoints.append(wp)

    if not waypoints:
        raise HTTPException(
            status_code=503,
            detail="No se pudo obtener datos meteorológicos para la ruta",
        )

    resp = _aggregate_route(waypoints)
    fuentes = {wp.fuente for wp in waypoints}
    degraded = aemet_preferred and "openmeteo" in fuentes and aemet_used < len(waypoints)
    warnings = []
    if degraded:
        warnings.append({"code": "DEPENDENCY_DEGRADED", "message": "AEMET preferida/no totalmente disponible; se usó fallback parcial o total según waypoint"})
    resp.capability_id = "climate.route_weather"
    resp.correlation_id = correlation_id
    resp.status = "ok"
    resp.data_status = "estimated"
    resp.provenance = {"fuentes": sorted(fuentes), "aemet_preferred": aemet_preferred, "aemet_waypoints": aemet_used, "total_waypoints": len(waypoints)}
    resp.warnings = warnings
    resp.errors = []
    core = resp.model_dump(exclude={"result"}) if hasattr(resp, "model_dump") else {k: v for k, v in resp.dict().items() if k != "result"}
    resp.result = core
    audit_integration(request, resp.contract_version, "ok", {"hazard": resp.hazard_level, "correlation_id": correlation_id, "degraded": degraded})
    return resp
