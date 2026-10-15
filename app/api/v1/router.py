from fastapi import APIRouter

from app.api.v1 import alerts, auth, clima, comparison, dashboard, geo, health, records

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(clima.router, prefix="/clima", tags=["Clima"])
router.include_router(geo.router, prefix="/geo", tags=["Geolocalizacion"])
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(alerts.router, prefix="/alertas", tags=["Alertas"])
router.include_router(records.router, prefix="/registros", tags=["Registros"])
router.include_router(comparison.router, prefix="/comparar", tags=["Comparacion"])
router.include_router(dashboard.router, tags=["Dashboard"])
