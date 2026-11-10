import os
from pathlib import Path

from sqlalchemy import inspect

from app.db.base import Base
from app.db.models import (
    Alerta,
    Estacion,
    FuenteDato,
    Medicion,
    Municipio,
    UmbralAlerta,
    Usuario,
    Zona,
)
from app.db.session import SessionLocal, engine, get_db

__all__ = [
    "Alerta",
    "Base",
    "Estacion",
    "FuenteDato",
    "Medicion",
    "Municipio",
    "SessionLocal",
    "UmbralAlerta",
    "Usuario",
    "Zona",
    "engine",
    "get_db",
    "init_db",
    "upgrade_db",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def upgrade_db() -> None:
    """Apply Alembic migrations when available; fallback to metadata create_all."""
    root = _project_root()
    alembic_ini = root / "alembic.ini"
    versions_dir = root / "alembic" / "versions"

    if alembic_ini.exists() and versions_dir.exists():
        try:
            from alembic import command
            from alembic.config import Config

            cfg = Config(str(alembic_ini))
            cfg.set_main_option("script_location", str(root / "alembic"))
            # Ensure runtime URL matches app settings
            from app.config.settings import settings

            cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

            inspector = inspect(engine)
            tables = set(inspector.get_table_names())
            if "alembic_version" not in tables and tables:
                # Existing DB created via create_all: baseline stamp to avoid re-creating tables
                command.stamp(cfg, "head")
                return
            command.upgrade(cfg, "head")
            return
        except Exception:
            # Fallback keeps bootstrap/tests working even without alembic runtime deps
            pass

    Base.metadata.create_all(bind=engine)


def init_db():
    upgrade_db()
    db = SessionLocal()
    try:
        from app.db.seed import seed_initial_data
        seed_initial_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada.")

