from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime
import time
import logging

from app.db.session import get_db
from app.db.models import Medicion, Usuario
from app.auth.jwt_auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

_metrics = {"requests_total": 0, "requests_by_endpoint": {}, "start_time": time.time()}


def _increment(endpoint: str):
    _metrics["requests_total"] += 1
    if endpoint not in _metrics["requests_by_endpoint"]:
        _metrics["requests_by_endpoint"][endpoint] = 0
    _metrics["requests_by_endpoint"][endpoint] += 1


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    uptime_seconds: int
    requests_total: int
    requests_by_endpoint: dict


class StatsResponse(BaseModel):
    status: str = "ok"
    timestamp: str
    metricas_api: dict
    datos: dict


@router.get("", response_model=HealthResponse)
async def health_check():
    _increment("/health")
    return HealthResponse(
        timestamp=datetime.now().isoformat(),
        uptime_seconds=int(time.time() - _metrics["start_time"]),
        requests_total=_metrics["requests_total"],
        requests_by_endpoint=_metrics["requests_by_endpoint"],
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    _increment("/stats")

    registros = db.query(Medicion).filter(
        func.date(Medicion.fecha) == datetime.now().date()
    ).all()

    temps = [r.temperatura for r in registros if r.temperatura is not None]
    hums = [r.humedad for r in registros if r.humedad is not None]

    return StatsResponse(
        timestamp=datetime.now().isoformat(),
        metricas_api={
            "requests_total": _metrics["requests_total"],
            "uptime_seconds": int(time.time() - _metrics["start_time"]),
        },
        datos={
            "registros_hoy": len(registros),
            "temp_promedio": round(sum(temps) / len(temps), 1) if temps else None,
            "humedad_promedio": round(sum(hums) / len(hums), 1) if hums else None,
        },
    )