import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OpenWeatherService:
    def __init__(self):
        self.base_url = settings.OPENWEATHER_BASE_URL
        self.api_key = settings.OPENWEATHER_API_KEY
        self.timeout = settings.AEMET_TIMEOUT

    async def get_weather(
        self, lat: Optional[float] = None, lon: Optional[float] = None, city: Optional[str] = None
    ) -> Optional[dict]:
        if not self.api_key:
            logger.info("OpenWeather: no API key configured")
            return None

        try:
            params = {"appid": self.api_key, "units": "metric", "lang": "es"}
            if lat is not None and lon is not None:
                params["lat"] = lat
                params["lon"] = lon
            elif city:
                params["q"] = f"{city},ES"
            else:
                params["q"] = "Madrid,ES"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(f"{self.base_url}/weather", params=params)
                if resp.status_code != 200:
                    logger.warning(f"OpenWeather: HTTP {resp.status_code}")
                    return None
                data = resp.json()

            return {
                "estacion_id": 0,
                "estacion_nombre": f"OpenWeather - {data.get('name', city or 'Desconocido')}",
                "distancia_km": 0.0,
                "data": {
                    "temperatura": data.get("main", {}).get("temp"),
                    "humedad": data.get("main", {}).get("humidity"),
                    "viento": self._ms_to_kmh(data.get("wind", {}).get("speed")),
                    "lluvia": data.get("rain", {}).get("1h", 0.0) if data.get("rain") else 0.0,
                    "presion": data.get("main", {}).get("pressure"),
                    "municipio": data.get("name", city or "Madrid"),
                    "provincia": "OpenWeatherMap",
                },
            }
        except Exception as e:
            logger.error(f"OpenWeather error: {e}")
            return None

    def _ms_to_kmh(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            return round(float(val) * 3.6, 2)
        except (ValueError, TypeError):
            return None
