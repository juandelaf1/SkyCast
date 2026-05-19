from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.geolocation_service import GeolocationService
from app.auth.jwt_auth import get_current_user
from app.db.models import Usuario

router = APIRouter()
logger = logging.getLogger(__name__)
geo_service = GeolocationService()


class GeoResponse(BaseModel):
    ciudad: str
    lat: float
    lon: float
    provincia: Optional[str] = None
    pais: Optional[str] = None
    fuente: str


@router.get("/{ciudad}", response_model=GeoResponse)
async def geocode_city(
    ciudad: str,
    current_user: Usuario = Depends(get_current_user),
):
    try:
        info = await geo_service.get_city_info(ciudad)
        if not info:
            raise HTTPException(status_code=404, detail=f"Ciudad no encontrada: {ciudad}")
        return GeoResponse(**info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocode: {e}")
        raise HTTPException(status_code=500, detail=str(e))