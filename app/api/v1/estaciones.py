import logging
import asyncio
import hashlib
from datetime import datetime

import numpy as np
from fastapi import APIRouter, Depends

from app.auth.jwt_auth import get_current_user
from app.services.aemet_service import AemetService
from app.services.openweather_service import OpenWeatherService

logger = logging.getLogger(__name__)
router = APIRouter()

GLOBAL_CITIES = [
    {"id": "nyc", "nombre": "Nueva York", "pais": "EEUU", "lat": 40.7128, "lon": -74.0060},
    {"id": "london", "nombre": "Londres", "pais": "Reino Unido", "lat": 51.5074, "lon": -0.1278},
    {"id": "tokyo", "nombre": "Tokio", "pais": "Japon", "lat": 35.6762, "lon": 139.6503},
    {"id": "paris", "nombre": "Paris", "pais": "Francia", "lat": 48.8566, "lon": 2.3522},
    {"id": "berlin", "nombre": "Berlin", "pais": "Alemania", "lat": 52.5200, "lon": 13.4050},
    {"id": "rome", "nombre": "Roma", "pais": "Italia", "lat": 41.9028, "lon": 12.4964},
    {"id": "sydney", "nombre": "Sydney", "pais": "Australia", "lat": -33.8688, "lon": 151.2093},
    {"id": "beijing", "nombre": "Pekin", "pais": "China", "lat": 39.9042, "lon": 116.4074},
    {"id": "moscow", "nombre": "Moscu", "pais": "Rusia", "lat": 55.7558, "lon": 37.6173},
    {"id": "dubai", "nombre": "Dubai", "pais": "EAU", "lat": 25.2048, "lon": 55.2708},
    {"id": "buenosaires", "nombre": "Buenos Aires", "pais": "Argentina", "lat": -34.6037, "lon": -58.3816},
    {"id": "mexico", "nombre": "Ciudad de Mexico", "pais": "Mexico", "lat": 19.4326, "lon": -99.1332},
    {"id": "lima", "nombre": "Lima", "pais": "Peru", "lat": -12.0464, "lon": -77.0428},
    {"id": "santiago", "nombre": "Santiago", "pais": "Chile", "lat": -33.4489, "lon": -70.6693},
    {"id": "bogota", "nombre": "Bogota", "pais": "Colombia", "lat": 4.7110, "lon": -74.0721},
    {"id": "lisbon", "nombre": "Lisboa", "pais": "Portugal", "lat": 38.7223, "lon": -9.1393},
    {"id": "shanghai", "nombre": "Shanghai", "pais": "China", "lat": 31.2304, "lon": 121.4737},
    {"id": "madrid", "nombre": "Madrid", "pais": "Espana", "lat": 40.4168, "lon": -3.7038},
    {"id": "barcelona", "nombre": "Barcelona", "pais": "Espana", "lat": 41.3874, "lon": 2.1686},
    {"id": "valencia", "nombre": "Valencia", "pais": "Espana", "lat": 39.4699, "lon": -0.3763},
    {"id": "sevilla", "nombre": "Sevilla", "pais": "Espana", "lat": 37.3891, "lon": -5.9845},
    {"id": "bilbao", "nombre": "Bilbao", "pais": "Espana", "lat": 43.2630, "lon": -2.9350},
]


async def _fetch_owm_city(city: dict, ow: OpenWeatherService) -> dict:
    try:
        result = await ow.get_weather(lat=city["lat"], lon=city["lon"])
        if result and result.get("data"):
            d = result["data"]
            return {
                "id": city["id"],
                "nombre": city["nombre"],
                "provincia": city.get("pais", ""),
                "lat": city["lat"],
                "lon": city["lon"],
                "temperatura": d.get("temperatura"),
                "humedad": d.get("humedad"),
                "viento": d.get("viento"),
                "lluvia": d.get("lluvia", 0),
                "presion": d.get("presion"),
                "alerta": "verde",
                "fuente": "OpenWeatherMap",
            }
    except Exception:
        pass
    return None


def _estimate_city(city: dict, rng: np.random.Generator) -> dict:
    return {
        "id": city["id"],
        "nombre": city["nombre"],
        "provincia": city.get("pais", ""),
        "lat": city["lat"],
        "lon": city["lon"],
        "temperatura": round(22 + rng.normal(0, 5), 1),
        "humedad": round(min(max(50 + rng.normal(0, 15), 0), 100), 1),
        "viento": round(max(rng.normal(15, 10), 0), 1),
        "lluvia": round(max(rng.exponential(0.5), 0), 2),
        "presion": round(1015 + rng.normal(0, 5), 1),
        "alerta": "verde",
        "fuente": "estimado",
    }


@router.get("")
async def get_estaciones(user=Depends(get_current_user)):
    ow = OpenWeatherService()
    stations = []

    if ow.api_key:
        tasks = [_fetch_owm_city(c, ow) for c in GLOBAL_CITIES]
        results = await asyncio.gather(*tasks)
        for city_data, city in zip(results, GLOBAL_CITIES):
            if city_data:
                stations.append(city_data)
    else:
        seed = int(hashlib.md5(datetime.now().strftime("%Y-%m-%d-%H").encode()).hexdigest(), 16) % 1000
        rng = np.random.default_rng(seed)
        for city in GLOBAL_CITIES:
            stations.append(_estimate_city(city, rng))

    aemet = AemetService()
    if aemet.api_key:
        try:
            aemet_stations = await asyncio.wait_for(
                aemet.fetch_all_stations(), timeout=5.0
            )
            existing_ids = {s["id"] for s in stations}
            for s in aemet_stations:
                if s["id"] not in existing_ids:
                    stations.append(s)
        except asyncio.TimeoutError:
            logger.warning("AEMET all-stations timeout, skipping")
        except Exception as e:
            logger.warning(f"AEMET all-stations error: {e}")

    return stations
