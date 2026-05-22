from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.services.aemet_service import AemetService
from app.services.alert_service import AlertService
from app.auth.jwt_auth import get_current_user
from app.db.models import Usuario, Medicion

router = APIRouter()
logger = logging.getLogger(__name__)
aemet = AemetService()
alerts = AlertService()


class ClimaResponse(BaseModel):
    status: str = "ok"
    municipio: str
    provincia: str
    fecha: str
    temperatura: Optional[float]
    humedad: Optional[float]
    viento: Optional[float]
    lluvia: Optional[float]
    presion: Optional[float]
    alertas: list
    alerta_nivel: Optional[str]
    estacion_nombre: Optional[str]
    estacion_distancia_km: Optional[float]
    fuente: str


@router.get("", response_model=ClimaResponse)
async def get_clima(
    lat: Optional[float] = Query(None, ge=-90, le=90),
    lon: Optional[float] = Query(None, ge=-180, le=180),
    ciudad: Optional[str] = Query(None, min_length=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if not lat and not lon and not ciudad:
        from app.services.geolocation_service import GeolocationService
        geo = GeolocationService()
        ip_data = geo.get_location_by_ip()
        if ip_data:
            lat = ip_data.get("lat")
            lon = ip_data.get("lon")
            ciudad = ip_data.get("ciudad")

    try:
        result = await aemet.get_weather(lat=lat, lon=lon, city=ciudad)

        if not result:
            raise HTTPException(status_code=503, detail="Sin datos meteorológicos disponibles")

        data = result.get("data", {})
        alertas_activas = alerts.get_alertas_activas(data)
        nivel_max = alerts.get_nivel_maximo(data)

        response = {
            "status": "ok",
            "municipio": data.get("municipio", ciudad or "Desconocido"),
            "provincia": data.get("provincia", "Madrid"),
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "temperatura": data.get("temperatura"),
            "humedad": data.get("humedad"),
            "viento": data.get("viento"),
            "lluvia": data.get("lluvia"),
            "presion": data.get("presion"),
            "alertas": alertas_activas,
            "alerta_nivel": nivel_max,
            "estacion_nombre": data.get("estacion_nombre"),
            "estacion_distancia_km": data.get("distancia_km"),
            "fuente": "AEMET",
        }

        med = Medicion(
            estacion_id=result.get("estacion_id", 1),
            fecha=datetime.now(),
            temperatura=data.get("temperatura"),
            humedad=data.get("humedad"),
            viento=data.get("viento"),
            lluvia=data.get("lluvia"),
            presion=data.get("presion"),
            fuente_id=1,
        )
        db.add(med)
        db.commit()

        return response

    except Exception as e:
        logger.error(f"Error get_clima: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ciudad}", response_model=ClimaResponse)
async def get_clima_ciudad(
    ciudad: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    return await get_clima(ciudad=ciudad, db=db, current_user=current_user)