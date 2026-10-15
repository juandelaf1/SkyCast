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
]


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.db.seed import seed_initial_data
        seed_initial_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos inicializada.")
