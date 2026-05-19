import pandas as pd
import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)


def transform_data(raw_data: list[dict]) -> pd.DataFrame:
    logger.info("Iniciando transformación de datos...")
    df = pd.DataFrame(raw_data)

    if df.empty:
        logger.warning("DataFrame vacío")
        return df

    df = df.dropna(how="all")

    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    numeric_cols = ["temperatura", "humedad", "viento", "lluvia", "presion"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["municipio", "ciudad", "estacion_nombre"]:
        if col in df.columns:
            df[col] = df[col].fillna("Desconocido")
            df[col] = df[col].str.strip().str.title()

    if "municipio" in df.columns:
        df["municipio"] = df["municipio"].replace("Madrid", "Centro")

    if "alertas" in df.columns:
        df["alertas"] = df["alertas"].apply(lambda x: x if isinstance(x, list) else [])

    before = len(df)
    dup_cols = [c for c in ["fecha", "municipio"] if c in df.columns]
    if dup_cols:
        df = df.drop_duplicates(subset=dup_cols, keep="last")
    after = len(df)
    logger.info(f"Duplicados eliminados: {before - after}")

    if "fecha" in df.columns:
        df = df[df["fecha"].notna() & (df["fecha"].dt.date <= date.today())]

    logger.info(f"Transformación completada: {len(df)} registros limpios")
    return df


def normalize_zone_name(name: str) -> str:
    name = name.strip().title()
    mapping = {
        "Madrid": "Centro",
        "Alcala De Henares": "Este",
        "Alcalá De Henares": "Este",
        "Mostoles": "Sur",
        "Móstoles": "Sur",
        "Fuenlabrada": "Sur",
        "Getafe": "Sur",
        "Alcorcon": "Sur",
        "Alcorcón": "Sur",
        "Torrejon De Ardoz": "Este",
        "Torrejón De Ardoz": "Este",
        "Parla": "Sur",
    }
    return mapping.get(name, name)