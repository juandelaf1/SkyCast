from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models import UmbralAlerta, Usuario
from app.auth.jwt_auth import get_current_user
from app.services.aemet_service import AemetService

router = APIRouter()
logger = logging.getLogger(__name__)


class UmbralResponse(BaseModel):
    id: int
    variable: str
    nivel: str
    valor: float
    descripcion: Optional[str] = None
    color_hex: Optional[str] = None
    icono: Optional[str] = None


class AlertUpdate(BaseModel):
    variable: str
    nivel: str
    valor: float
    descripcion: Optional[str] = None
    color_hex: Optional[str] = None
    icono: Optional[str] = None


@router.get("", response_model=list[UmbralResponse])
def get_alertas(
    variable: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query = db.query(UmbralAlerta)
    if variable:
        query = query.filter(UmbralAlerta.variable == variable)
    return query.all()


@router.post("")
def create_or_update_alerta(
    alerta: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    existing = db.query(UmbralAlerta).filter(
        UmbralAlerta.variable == alerta.variable,
        UmbralAlerta.nivel == alerta.nivel,
    ).first()

    if existing:
        existing.valor = alerta.valor
        existing.descripcion = alerta.descripcion
        existing.color_hex = alerta.color_hex
        existing.icono = alerta.icono
    else:
        existing = UmbralAlerta(**alerta.model_dump())
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return {"status": "ok", "umbral": existing}


@router.get("/oficiales")
async def get_aemet_official_alerts(
    current_user: Usuario = Depends(get_current_user),
):
    aemet = AemetService()
    alerts = await aemet.fetch_official_alerts()
    return {
        "fuente": "AEMET OpenData",
        "total": len(alerts),
        "alertas": alerts,
    }