from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.aemet_service import AemetService
from app.services.alert_service import AlertService
from app.db.models import Medicion, Estacion, FuenteDato
from datetime import datetime

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def fetch_aemet_data(db: Session):
    try:
        logger.info("Scheduler: Fetching AEMET data...")
        aemet = AemetService()
        _alerts = AlertService()

        estaciones = db.query(Estacion).filter(
            Estacion.municipio_id.isnot(None)
        ).limit(3).all()

        if not estaciones:
            est = db.query(Estacion).first()
            if est:
                estaciones = [est]

        for est in estaciones:
            try:
                result = aemet.get_weather(lat=float(est.lat), lon=float(est.lon))
                if not result:
                    continue

                data = result.get("data", {})
                if not data:
                    continue

                fuente = db.query(FuenteDato).filter(FuenteDato.codigo == "aemet").first()

                existing = (
                    db.query(Medicion)
                    .filter(Medicion.estacion_id == est.id)
                    .filter(Medicion.fecha >= datetime.now().replace(hour=0, minute=0, second=0))
                    .first()
                )
                if existing:
                    logger.info(f"Datos ya existentes para estación {est.nombre}")
                    continue

                med = Medicion(
                    estacion_id=est.id,
                    fecha=datetime.now(),
                    temperatura=data.get("temperatura"),
                    humedad=data.get("humedad"),
                    viento=data.get("viento"),
                    lluvia=data.get("lluvia"),
                    presion=data.get("presion"),
                    fuente_id=fuente.id if fuente else None,
                )
                db.add(med)
                db.commit()
                logger.info(f"Datos guardados para {est.nombre}: {data.get('temperatura')}C")
            except Exception as e:
                logger.error(f"Error fetching data for station {est.nombre}: {e}")
                db.rollback()

    except Exception as e:
        logger.error(f"Error en scheduler: {e}")


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        fetch_aemet_data,
        trigger=IntervalTrigger(minutes=120),
        args=[SessionLocal()],
        id="fetch_aemet_data",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler iniciado: fetch cada 2 horas")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler detenido")