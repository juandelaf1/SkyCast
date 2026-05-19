import httpx
import logging
from typing import Optional
from app.config.settings import settings

logger = logging.getLogger(__name__)


class GeolocationService:
    def __init__(self):
        self.ip_api_url = settings.IP_API_URL
        self.nominatim_url = settings.NOMINATIM_URL
        self._cache = {}

    async def get_city_info(self, city: str) -> Optional[dict]:
        cache_key = f"city:{city.lower()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            params = {"q": city, "format": "json", "limit": 1}
            headers = {"User-Agent": "SkyCast-Climate/1.0"}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.nominatim_url}/search", params=params, headers=headers)
                if resp.status_code != 200 or not resp.json():
                    return None

                data = resp.json()[0]
                lat = float(data.get("lat", 0))
                lon = float(data.get("lon", 0))

                address = data.get("address", {})
                provincia = address.get("state") or address.get("region", "")
                pais = address.get("country_code", "").upper()

                result = {
                    "ciudad": city,
                    "lat": lat,
                    "lon": lon,
                    "provincia": provincia,
                    "pais": pais,
                    "fuente": "nominatim",
                }
                self._cache[cache_key] = result
                return result
        except Exception as e:
            logger.error(f"Error geocoding city: {e}")
            return None

    def get_location_by_ip(self) -> Optional[dict]:
        try:
            if self._cache.get("ip"):
                return self._cache["ip"]
            import requests
            resp = requests.get(self.ip_api_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    result = {
                        "lat": data.get("lat"),
                        "lon": data.get("lon"),
                        "ciudad": data.get("city", ""),
                        "provincia": data.get("regionName", ""),
                        "pais": data.get("countryCode", ""),
                        "fuente": "ip-api",
                    }
                    self._cache["ip"] = result
                    return result
        except Exception as e:
            logger.error(f"Error IP geolocation: {e}")
        return {"lat": 40.4168, "lon": -3.7038, "ciudad": "Unknown", "provincia": "", "pais": "", "fuente": "default"}

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[dict]:
        try:
            params = {"lat": lat, "lon": lon, "format": "json"}
            headers = {"User-Agent": "SkyCast-Climate/1.0"}

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{self.nominatim_url}/reverse", params=params, headers=headers)
                if resp.status_code != 200:
                    return None

                data = resp.json()
                address = data.get("address", {})
                return {
                    "ciudad": address.get("city") or address.get("town") or address.get("village", "Unknown"),
                    "provincia": address.get("state", ""),
                    "codigo_postal": address.get("postcode"),
                    "pais": address.get("country_code", "").upper(),
                }
        except Exception as e:
            logger.error(f"Error reverse geocoding: {e}")
            return None