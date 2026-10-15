import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_data(file_path: str) -> list[dict] | None:
    try:
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Archivo no encontrado: {file_path}")
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Datos extraídos: {len(data)} registros")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error en extracción: {e}")
        return None


def extract_from_db(session, model, filters: dict | None = None) -> list:
    try:
        from sqlalchemy import select
        query = select(model)
        if filters:
            for col, val in filters.items():
                query = query.where(getattr(model, col) == val)
        result = session.execute(query)
        return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error extrayendo de DB: {e}")
        return []
