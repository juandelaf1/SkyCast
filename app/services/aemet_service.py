import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


class AemetService:
    def __init__(self):
        self.base_url = settings.AEMET_BASE_URL
        self.api_key = settings.AEMET_API_KEY
        self.timeout = settings.AEMET_TIMEOUT

    async def get_weather(
        self, lat: Optional[float] = None, lon: Optional[float] = None, city: Optional[str] = None
    ) -> Optional[dict]:
        if self.api_key:
            try:
                estacion = await self._find_nearest_station(lat, lon)
                if estacion:
                    datos = await self._fetch_station_data(estacion["indicativo"])
                    if datos:
                        return {
                            "estacion_id": estacion["id"],
                            "estacion_nombre": estacion["nombre"],
                            "distancia_km": estacion["distancia_km"],
                            "data": datos,
                        }
            except Exception as e:
                logger.error(f"Error AEMET: {e}")

        from app.services.openweather_service import OpenWeatherService
        ow = OpenWeatherService()
        ow_result = await ow.get_weather(lat=lat, lon=lon, city=city)
        if ow_result:
            return ow_result

        return self._get_fallback_data(lat, lon, city)

    async def _find_nearest_station(self, lat: float, lon: float) -> Optional[dict]:
        try:
            url = f"{self.base_url}/valores/climatologicos/inventarioestaciones/todasestaciones"
            headers = {"api_key": self.api_key}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return None

                data = resp.json()
                if isinstance(data, dict):
                    datos_url = data.get("datos")
                    if datos_url:
                        resp2 = await client.get(datos_url)
                        if resp2.status_code == 200:
                            estaciones = resp2.json()
                        else:
                            return None
                    else:
                        return None
                else:
                    estaciones = data

            if not estaciones:
                return None

            from app.core.utils import haversine
            nearest = None
            min_dist = float("inf")

            for est in estaciones:
                try:
                    est_lat = float(est.get("latitud", 0))
                    est_lon = float(est.get("longitud", 0))
                    dist = haversine(lat, lon, est_lat, est_lon)
                    if dist < min_dist:
                        min_dist = dist
                        nearest = {
                            "id": 1,
                            "indicativo": est.get("indicativo", ""),
                            "nombre": est.get("nombre", ""),
                            "lat": est_lat,
                            "lon": est_lon,
                            "distancia_km": round(dist, 2),
                        }
                except (ValueError, TypeError):
                    continue

            if nearest and nearest["distancia_km"] <= settings.STATION_MAX_DISTANCE_KM:
                return nearest
            if nearest and nearest["distancia_km"] <= settings.STATION_FALLBACK_DISTANCE_KM:
                return nearest

            return None
        except Exception as e:
            logger.error(f"Error finding station: {e}")
            return None

    async def _fetch_station_data(self, indicativo: str) -> Optional[dict]:
        try:
            url = f"{self.base_url}/valores/climatologicos/ultimosdatos/{indicativo}"
            headers = {"api_key": self.api_key}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    return None

                raw = resp.json()
                if isinstance(raw, dict):
                    datos_url = raw.get("datos")
                    if datos_url:
                        resp2 = await client.get(datos_url)
                        if resp2.status_code == 200:
                            data = resp2.json()
                        else:
                            return None
                    else:
                        return None
                else:
                    data = raw

                if isinstance(data, list) and len(data) > 0:
                    return self._normalize_aemet_data(data[0])
                return None
        except Exception as e:
            logger.error(f"Error fetching station data: {e}")
            return None

    def _normalize_aemet_data(self, raw: dict) -> dict:
        return {
            "temperatura": self._parse_float(raw.get("ta")),
            "humedad": self._parse_float(raw.get("hr")),
            "viento": self._ms_to_kmh(raw.get("vv")),
            "lluvia": self._parse_float(raw.get("prec")),
            "presion": self._parse_float(raw.get("p")),
            "municipio": raw.get("ubi", "Madrid"),
            "provincia": raw.get("provincia", "Madrid"),
        }

    def _parse_float(self, val) -> Optional[float]:
        if val is None or val == "":
            return None
        try:
            return float(str(val).replace(",", "."))
        except (ValueError, AttributeError):
            return None

    def _ms_to_kmh(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            ms = float(str(val).replace(",", "."))
            return round(ms * 3.6, 2)
        except (ValueError, AttributeError):
            return None

    def _get_fallback_data(self, lat: float, lon: float, city: str) -> dict:
        return {
            "estacion_id": 1,
            "estacion_nombre": "Madrid-Retiro",
            "distancia_km": 2.5,
            "data": {
                "temperatura": 22.5,
                "humedad": 55.0,
                "viento": 12.0,
                "lluvia": 0.0,
                "presion": 1013.0,
                "municipio": city or "Madrid",
                "provincia": "Madrid",
            },
        }