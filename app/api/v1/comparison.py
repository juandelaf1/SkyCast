from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import logging

from app.db.session import get_db
from app.db.models import Medicion, Usuario, FuenteDato
from app.auth.jwt_auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class ComparisonRequest(BaseModel):
    temperatura_manual: float
    humedad_manual: float
    viento_manual: float
    lluvia_manual: float
    fecha: Optional[str] = None
    municipio: str


class ComparisonResult(BaseModel):
    municipio: str
    fecha: str
    fuente_aemet: Optional[dict]
    fuente_manual: dict
    discrepancias: dict
    alertas: list


THRESHOLDS = {
    "temperatura": 3.0,
    "humedad": 10.0,
    "viento": 10.0,
    "lluvia": 5.0,
}


@router.post("", response_model=ComparisonResult)
def compare_manual_vs_aemet(
    req: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        if req.fecha:
            fecha_dt = datetime.strptime(req.fecha, "%Y-%m-%d")
        else:
            fecha_dt = datetime.now()
    except ValueError:
        raise HTTPException(status_code=400, detail="Fecha inválida. Formato: YYYY-MM-DD")

    aemet_fuente = db.query(FuenteDato).filter(FuenteDato.codigo == "aemet").first()
    if not aemet_fuente:
        raise HTTPException(status_code=500, detail="Fuente AEMET no encontrada en base de datos")

    aemet_med = (
        db.query(Medicion)
        .filter(Medicion.fecha >= fecha_dt.replace(hour=0, minute=0, second=0))
        .filter(Medicion.fecha <= fecha_dt.replace(hour=23, minute=59, second=59))
        .filter(Medicion.fuente_id == aemet_fuente.id)
        .first()
    )

    aemet_data = None
    if aemet_med:
        aemet_data = {
            "temperatura": float(aemet_med.temperatura) if aemet_med.temperatura else None,
            "humedad": float(aemet_med.humedad) if aemet_med.humedad else None,
            "viento": float(aemet_med.viento) if aemet_med.viento else None,
            "lluvia": float(aemet_med.lluvia) if aemet_med.lluvia else None,
        }

    manual_data = {
        "temperatura": req.temperatura_manual,
        "humedad": req.humedad_manual,
        "viento": req.viento_manual,
        "lluvia": req.lluvia_manual,
    }

    discrepancias = {}
    alertas = []

    if aemet_data:
        for var in ["temperatura", "humedad", "viento", "lluvia"]:
            aemet_val = aemet_data.get(var)
            manual_val = manual_data.get(var)
            if aemet_val is not None and manual_val is not None:
                diff = abs(manual_val - aemet_val)
                discrepancias[var] = {
                    "manual": manual_val,
                    "aemet": aemet_val,
                    "diferencia": round(diff, 2),
                    "umbral": THRESHOLDS[var],
                    "supera_umbral": diff > THRESHOLDS[var],
                }
                if diff > THRESHOLDS[var]:
                    alertas.append(f"Diferencia en {var}: {diff:.2f} (umbral: {THRESHOLDS[var]})")
    else:
        for var in ["temperatura", "humedad", "viento", "lluvia"]:
            alertas.append(f"No hay datos AEMET para comparar {var}")

    return ComparisonResult(
        municipio=req.municipio,
        fecha=fecha_dt.strftime("%Y-%m-%d"),
        fuente_aemet=aemet_data,
        fuente_manual=manual_data,
        discrepancias=discrepancias,
        alertas=alertas,
    )