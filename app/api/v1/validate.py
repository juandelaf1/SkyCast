import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.audit import audit_integration
from app.core.m2m import require_m2m_if_configured
from app.core.rate_limit import rate_limit
from app.services.aemet_service import AemetService
from app.core.utils import haversine, parse_aemet_coordinate

router = APIRouter()
logger = logging.getLogger(__name__)
aemet = AemetService()

# Radio de búsqueda de estaciones cercanas (km)
VALIDATION_RADIUS_KM = 20.0
MAX_STATIONS = 5

# URL base de Open-Meteo (fallback sin API key)
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"


class ObservationReport(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitud del informe")
    lon: float = Field(..., ge=-180, le=180, description="Longitud del informe")
    reporte: str = Field(..., min_length=1, description="Descripción del fenómeno reportado")
    temperatura_c: Optional[float] = Field(None, description="Temperatura reportada por el usuario")
    timestamp: Optional[str] = Field(None, description="Timestamp del informe")
    fuente_reporte: Optional[str] = Field("usuario", description="Quién reportó (transportista, ciudadano, etc.)")


class StationMatch(BaseModel):
    id: Optional[str] = None
    nombre: str
    distancia_km: float
    temperatura_c: Optional[float] = None
    confirma_helada: bool = False
    fuente_temperatura: str = "desconocida"  # "aemet" | "openmeteo" | "ninguna"


class ValidationResponse(BaseModel):
    contract_version: str = "skycast-validate-observation/0.1"
    valido: bool
    confianza: int = Field(..., ge=0, le=100, description="Porcentaje de confianza 0-100")
    estaciones_cercanas: list[StationMatch]
    nota: str
    procedencia: str = "estimado (validacion cruzada contra estaciones/fuentes; no es medicion directa)"


@router.post("/validate-observation", response_model=ValidationResponse, tags=["Validación"])
async def validate_observation(
    report: ObservationReport,
    request: Request,
    _m2m: object = Depends(require_m2m_if_configured("weather:validate")),
    _rl: None = Depends(rate_limit("SKYCAST_M2M_RATE_LIMIT", "120/minute")),
):
    """
    Valida un informe de usuario (ej. transportista) contra estaciones cercanas.

    Convierte un aviso anecdótico en un dato validado y accionable.
    Útil para EnRuta: un reporte de "helada intensa" se confirma o descarta
    con datos oficiales antes de afectar al matching de rutas.

    Fuente de temperatura: intenta AEMET primero; si falla, usa Open-Meteo.
    """
    lat, lon = report.lat, report.lon
    temp_reportada = report.temperatura_c
    reporte_texto = (report.reporte or "").lower()

    # --- 1. Detectar si el usuario reporta helada ---
    reporta_helada = (
        "helada" in reporte_texto
        or "frost" in reporte_texto
        or "temperatura bajo cero" in reporte_texto
        or (temp_reportada is not None and temp_reportada <= 0)
    )

    # --- 2. Buscar estaciones AEMET cercanas ---
    estaciones = await _buscar_estaciones_cercanas(lat, lon)

    confirmaciones = 0
    matches = []

    for est in estaciones:
        indicativo = est.get("indicativo")
        est_lat = est.get("lat")
        est_lon = est.get("lon")
        nombre = est.get("nombre", "Desconocida")
        distancia = est.get("distancia_km", 0)

        temp_estacion = None
        fuente = "ninguna"

        # Intento 1: AEMET por indicativo de estación
        if indicativo:
            try:
                datos = await aemet._fetch_station_data(indicativo)
                if datos:
                    temp_estacion = datos.get("temperatura")
                    fuente = "aemet"
            except Exception as e:
                logger.warning(f"Error AEMET estación {indicativo}: {e}")

        # Intento 2: Open-Meteo por coordenadas de la estación (fallback)
        if temp_estacion is None and est_lat is not None and est_lon is not None:
            try:
                temp_om = await _get_openmeteo_temperature(est_lat, est_lon)
                if temp_om is not None:
                    temp_estacion = temp_om
                    fuente = "openmeteo"
            except Exception as e:
                logger.warning(f"Error Open-Meteo para {nombre}: {e}")

        # --- Evaluar confirmación ---
        confirma = False
        if temp_reportada is not None and temp_estacion is not None:
            # El usuario y la estación coinciden dentro de ±3°C
            confirma = abs(temp_reportada - temp_estacion) <= 3.0
        elif reporta_helada and temp_estacion is not None:
            # El usuario reporta helada y la estación confirma T <= 0
            confirma = temp_estacion <= 0.0

        if confirma:
            confirmaciones += 1

        matches.append(StationMatch(
            id=indicativo,
            nombre=nombre,
            distancia_km=distancia,
            temperatura_c=temp_estacion,
            confirma_helada=confirma,
            fuente_temperatura=fuente,
        ))

    # --- 3. Calcular confianza ---
    total = len(matches)
    if total == 0:
        confianza = 0
        valido = False
        nota = "No se encontraron estaciones cercanas para validar el informe."
    else:
        confianza = int(round((confirmaciones / total) * 100))
        valido = confirmaciones >= 1
        fuentes = set(m.fuente_temperatura for m in matches if m.fuente_temperatura != "ninguna")
        fuente_txt = ", ".join(fuentes) if fuentes else "ninguna"
        nota = f"{confirmaciones}/{total} estación(es) cercana(s) confirma(n) el informe (fuentes: {fuente_txt})."

    resp = ValidationResponse(
        valido=valido,
        confianza=confianza,
        estaciones_cercanas=matches,
        nota=nota,
    )
    audit_integration(request, resp.contract_version, "ok", {"valido": valido, "confianza": confianza})
    return resp


async def _get_openmeteo_temperature(lat: float, lon: float) -> Optional[float]:
    """Obtiene temperatura actual desde Open-Meteo (sin API key)."""
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            OPEN_METEO_BASE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m",
                "timezone": "auto",
            },
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("current", {}).get("temperature_2m")


async def _buscar_estaciones_cercanas(lat: float, lon: float) -> list[dict]:
    """
    Devuelve hasta MAX_STATIONS estaciones AEMET dentro de VALIDATION_RADIUS_KM,
    ordenadas por distancia.
    """
    try:
        url = f"{aemet.base_url}/valores/climatologicos/inventarioestaciones/todasestaciones"
        headers = {"api_key": aemet.api_key}

        import httpx
        async with httpx.AsyncClient(timeout=aemet.timeout) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                return []

            data = resp.json()
            if isinstance(data, dict):
                datos_url = data.get("datos")
                if datos_url:
                    resp2 = await client.get(datos_url)
                    if resp2.status_code != 200:
                        return []
                    import json
                    estaciones = json.loads(resp2.content.decode("ISO-8859-15"))
                else:
                    return []
            else:
                estaciones = data

        if not estaciones:
            return []

        candidatas = []
        for est in estaciones:
            try:
                est_lat = parse_aemet_coordinate(est.get("latitud"))
                est_lon = parse_aemet_coordinate(est.get("longitud"))
                if est_lat is None or est_lon is None:
                    continue
                dist = haversine(lat, lon, est_lat, est_lon)
                if dist <= VALIDATION_RADIUS_KM:
                    candidatas.append({
                        "id": None,
                        "indicativo": est.get("indicativo", ""),
                        "nombre": est.get("nombre", ""),
                        "lat": est_lat,
                        "lon": est_lon,
                        "distancia_km": round(dist, 2),
                    })
            except (ValueError, TypeError):
                continue

        candidatas.sort(key=lambda x: x["distancia_km"])
        return candidatas[:MAX_STATIONS]

    except Exception as e:
        logger.error(f"Error buscando estaciones cercanas: {e}")
        return []
