from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    AEMET_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    REDIS_URL: str = ""
    SECRET_KEY: str = "clave-temporal-cambiar-en-produccion"
    DATABASE_URL: str = "sqlite:///skycast.db"
    API_BASE: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"

    AEMET_TIMEOUT: int = 20
    CACHE_TTL_SECONDS: int = 1800
    GEOCACHE_TTL_SECONDS: int = 3600
    SCHEDULER_INTERVAL_MINUTES: int = 120

    RATE_LIMIT_CLIMA: int = 30
    RATE_LIMIT_GEO: int = 10
    RATE_LIMIT_WINDOW: int = 60

    STATION_MAX_DISTANCE_KM: float = 50.0
    STATION_FALLBACK_DISTANCE_KM: float = 100.0

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    IP_API_URL: str = "http://ip-api.com/json"
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    AEMET_BASE_URL: str = "https://opendata.aemet.es/opendata/api"
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    ALERT_TEMP_EXTREME: float = 40.0
    ALERT_TEMP_HIGH: float = 35.0
    ALERT_TEMP_COLD: float = 0.0
    ALERT_WIND_HIGH: float = 70.0
    ALERT_RAIN_HIGH: float = 30.0
    ALERT_HUMIDITY_HIGH: float = 90.0


settings = Settings()