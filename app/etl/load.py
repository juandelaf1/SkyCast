from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models import Medicion, Estacion, FuenteDato

logger = logging.getLogger(__name__)


def load_data(df, db: Session, source_code: str = "etl") -> int:
    logger.info("Iniciando carga de datos en DB...")

    fuente = db.query(FuenteDato).filter(FuenteDato.codigo == source_code).first()
    if not fuente:
        fuente = FuenteDato(codigo=source_code, nombre=source_code.upper(), cobertura="etl")
        db.add(fuente)
        db.commit()
        db.refresh(fuente)

    inserted = 0
    errors = 0

    for _, row in df.iterrows():
        try:
            indicativo = row.get("estacion_id") or row.get("indicativo")
            estacion = db.query(Estacion).filter(Estacion.indicativo == indicativo).first()

            if not estacion:
                logger.warning(f"Estación no encontrada: {indicativo}")
                continue

            fecha = row.get("fecha")
            if isinstance(fecha, str):
                fecha = pd_to_datetime(fecha)
            if fecha is None:
                fecha = datetime.now()

            existing = (
                db.query(Medicion)
                .filter(Medicion.estacion_id == estacion.id)
                .filter(Medicion.fecha == fecha)
                .first()
            )
            if existing:
                continue

            medicion = Medicion(
                estacion_id=estacion.id,
                fecha=fecha,
                temperatura=row.get("temperatura"),
                humedad=row.get("humedad"),
                viento=row.get("viento"),
                lluvia=row.get("lluvia"),
                presion=row.get("presion"),
                fuente_id=fuente.id,
            )
            db.add(medicion)
            db.commit()
            inserted += 1

        except Exception as e:
            logger.error(f"Error insertando registro: {e}")
            db.rollback()
            errors += 1

    logger.info(f"Carga completada: {inserted} insertados, {errors} errores")
    return inserted


def pd_to_datetime(val) -> datetime:
    import pandas as pd
    if isinstance(val, pd.Timestamp):
        return val.to_pydatetime()
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            return datetime.now()
    return datetime.now()


def run_pipeline(data_path: str, db: Session, source_code: str = "etl") -> dict:
    from app.etl.extract import extract_data
    from app.etl.transform import transform_data

    result = {"extracted": 0, "transformed": 0, "loaded": 0, "errors": 0}

    raw = extract_data(data_path)
    if not raw:
        result["errors"] += 1
        return result
    result["extracted"] = len(raw)

    df = transform_data(raw)
    if df.empty:
        result["errors"] += 1
        return result
    result["transformed"] = len(df)

    loaded = load_data(df, db, source_code)
    result["loaded"] = loaded

    return result


def run_pipeline_with_lineage(data_path: str, db: Session, source_code: str = "etl") -> dict:
    from app.core.lineage import LineageLogger
    from app.etl.extract import extract_data
    from app.etl.transform import transform_data

    lineage = LineageLogger(source=source_code)

    raw = extract_data(data_path)
    if not raw:
        lineage.log_extract(0, details="No data extracted from source")
        return {"lineage": lineage.summary(), "error": "No data extracted"}

    rows_extracted = len(raw)
    lineage.log_extract(rows_extracted, details=f"Extracted {rows_extracted} records from {data_path}")

    df = transform_data(raw)
    rows_before_transform = len(raw)
    rows_after_transform = len(df)
    rows_discarded = rows_before_transform - rows_after_transform
    lineage.log_transform(
        rows_in=rows_before_transform,
        rows_out=rows_after_transform,
        rows_discarded=rows_discarded,
        details=f"Transformed: {rows_discarded} rows discarded (duplicates, nulls, invalid)",
    )

    if df.empty:
        lineage.log_load(rows_in=0, rows_loaded=0, details="No rows to load after transform")
        return {"lineage": lineage.summary(), "error": "No data after transform"}

    loaded = load_data(df, db, source_code)
    duplicates = rows_after_transform - loaded
    lineage.log_load(
        rows_in=rows_after_transform,
        rows_loaded=loaded,
        rows_duplicates=duplicates,
        details=f"Loaded {loaded} rows ({duplicates} duplicates skipped)",
    )

    return {
        "lineage": lineage.summary(),
        "extracted": rows_extracted,
        "transformed": rows_after_transform,
        "loaded": loaded,
        "discarded": rows_discarded,
        "duplicates": duplicates,
    }