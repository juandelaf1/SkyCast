import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.jwt_auth import get_current_user
from app.core.validators import validar_registro
from app.db.models import Estacion, FuenteDato, Medicion, Usuario
from app.db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class RecordCreate(BaseModel):
    fecha: str | None = None
    temperatura: float = Field(..., ge=-50, le=60)
    humedad: float = Field(..., ge=0, le=100)
    viento: float = Field(ge=0)
    lluvia: float = Field(ge=0)
    presion: float | None = Field(None, ge=800, le=1200)
    estacion_id: int
    municipio: str | None = None
    lat: float | None = Field(None, ge=-90, le=90, description="Latitud del reporte (geovalidación)")
    lon: float | None = Field(None, ge=-180, le=180, description="Longitud del reporte (geovalidación)")


class RecordResponse(BaseModel):
    id: int
    estacion_id: int
    fecha: datetime
    temperatura: float | None
    humedad: float | None
    viento: float | None
    lluvia: float | None
    presion: float | None
    fuente: str = "manual"


class PaginatedRecords(BaseModel):
    items: list[RecordResponse]
    total: int
    page: int
    pages: int
    limit: int


@router.get("", response_model=PaginatedRecords)
def get_records(
    fecha: str | None = Query(None, description="YYYY-MM-DD"),
    municipio: str | None = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(Medicion)
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
            query = query.filter(func.date(Medicion.fecha) == fecha_dt.date())
        except ValueError:
            raise HTTPException(status_code=400, detail="Fecha inválida. Formato: YYYY-MM-DD")

    total = query.count()
    pages = max(1, (total + limit - 1) // limit)
    offset = (page - 1) * limit

    records = query.order_by(Medicion.fecha.desc()).offset(offset).limit(limit).all()
    items = []
    for med in records:
        items.append(RecordResponse(
            id=med.id,
            estacion_id=med.estacion_id,
            fecha=med.fecha,
            temperatura=float(med.temperatura) if med.temperatura else None,
            humedad=float(med.humedad) if med.humedad else None,
            viento=float(med.viento) if med.viento else None,
            lluvia=float(med.lluvia) if med.lluvia else None,
            presion=float(med.presion) if med.presion else None,
            fuente=med.fuente.codigo if med.fuente else "manual",
        ))

    return PaginatedRecords(items=items, total=total, page=page, pages=pages, limit=limit)


@router.post("", response_model=RecordResponse)
def create_record(
    record: RecordCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    validation_errors = validar_registro(record.model_dump())
    if validation_errors:
        raise HTTPException(status_code=400, detail={"errores": validation_errors})

    estacion = db.query(Estacion).filter(Estacion.id == record.estacion_id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no encontrada")

    if record.lat is not None and record.lon is not None:
        from app.core.utils import haversine
        dist = haversine(float(estacion.lat), float(estacion.lon), record.lat, record.lon)
        if dist > 10.0:
            raise HTTPException(
                status_code=400,
                detail=f"Geovalidación: tu ubicación está a {dist:.1f} km de la estación (máx 10 km)",
            )

    fuente = db.query(FuenteDato).filter(FuenteDato.codigo == "manual").first()

    fecha_dt = datetime.now()
    if record.fecha:
        try:
            fecha_dt = datetime.strptime(record.fecha, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Fecha inválida. Formato: YYYY-MM-DD")

    medicion = Medicion(
        estacion_id=record.estacion_id,
        fecha=fecha_dt,
        temperatura=record.temperatura,
        humedad=record.humedad,
        viento=record.viento,
        lluvia=record.lluvia,
        presion=record.presion,
        fuente_id=fuente.id if fuente else None,
    )
    db.add(medicion)
    db.commit()
    db.refresh(medicion)

    return RecordResponse(
        id=medicion.id,
        estacion_id=medicion.estacion_id,
        fecha=medicion.fecha,
        temperatura=medicion.temperatura,
        humedad=medicion.humedad,
        viento=medicion.viento,
        lluvia=medicion.lluvia,
        presion=medicion.presion,
        fuente="manual",
    )
