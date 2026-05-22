import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.hash import pbkdf2_sha256

from app.db.base import Base
from app.db.session import get_db
from app.db.models import Usuario, Zona, Municipio, Estacion, FuenteDato, UmbralAlerta
from app.main import app
from app.auth.jwt_auth import get_current_user
from app.config.settings import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_skycast.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _create_token(user_id: int, email: str) -> str:
    payload = {
        "sub": email,
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _seed_data(db):
    zonas_data = [
        {"codigo": "centro", "nombre": "Centro", "es_default": True},
        {"codigo": "norte", "nombre": "Norte", "es_default": False},
        {"codigo": "sur", "nombre": "Sur", "es_default": False},
    ]
    for z in zonas_data:
        db.add(Zona(**z))
    db.commit()
    zonas = {z.codigo: z.id for z in db.query(Zona).all()}

    municipios_data = [
        {"nombre": "Madrid", "cod_ine": "28079", "lat": 40.4168, "lon": -3.7038, "zona_id": zonas["centro"]},
        {"nombre": "Getafe", "cod_ine": "28065", "lat": 40.3057, "lon": -3.7300, "zona_id": zonas["sur"]},
    ]
    for m in municipios_data:
        db.add(Municipio(**m))
    db.commit()

    muni = {m.nombre: m for m in db.query(Municipio).all()}

    estaciones_data = [
        {"indicativo": "3195", "nombre": "Madrid-Retiro", "provincia": "Madrid", "lat": 40.4114, "lon": -3.6788, "municipio_id": muni["Madrid"].id},
        {"indicativo": "3200", "nombre": "Getafe", "provincia": "Madrid", "lat": 40.2947, "lon": -3.7214, "municipio_id": muni["Getafe"].id},
    ]
    for e in estaciones_data:
        db.add(Estacion(**e))
    db.commit()

    fuentes_data = [
        {"codigo": "aemet", "nombre": "AEMET OpenData", "url": "https://opendata.aemet.es", "cobertura": "España"},
        {"codigo": "openweather", "nombre": "OpenWeatherMap", "url": "https://api.openweathermap.org", "cobertura": "Global"},
        {"codigo": "manual", "nombre": "Registro Manual", "url": None, "cobertura": "Usuario"},
    ]
    for f in fuentes_data:
        db.add(FuenteDato(**f))
    db.commit()

    umbrales_data = [
        {"variable": "temperatura", "nivel": "rojo", "valor": 40.0, "descripcion": "Calor extremo", "color_hex": "#DC2626", "icono": "🔥"},
        {"variable": "temperatura", "nivel": "naranja", "valor": 35.0, "descripcion": "Calor alto", "color_hex": "#EA580C", "icono": "🟠"},
        {"variable": "viento", "nivel": "rojo", "valor": 70.0, "descripcion": "Viento muy fuerte", "color_hex": "#DC2626", "icono": "💨"},
        {"variable": "viento", "nivel": "naranja", "valor": 50.0, "descripcion": "Viento fuerte", "color_hex": "#EA580C", "icono": "💨"},
        {"variable": "lluvia", "nivel": "rojo", "valor": 30.0, "descripcion": "Lluvia intensa", "color_hex": "#DC2626", "icono": "🌧️"},
        {"variable": "lluvia", "nivel": "naranja", "valor": 15.0, "descripcion": "Lluvia moderada", "color_hex": "#EA580C", "icono": "🌧️"},
        {"variable": "humedad", "nivel": "rojo", "valor": 90.0, "descripcion": "Humedad muy alta", "color_hex": "#DC2626", "icono": "💧"},
        {"variable": "humedad", "nivel": "naranja", "valor": 80.0, "descripcion": "Humedad alta", "color_hex": "#EA580C", "icono": "💧"},
    ]
    for u in umbrales_data:
        db.add(UmbralAlerta(**u))
    db.commit()


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    _seed_data(db)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session):
    pw_hash = pbkdf2_sha256.hash("Test1234")
    user = Usuario(email="test@skycast.com", password_hash=pw_hash, password_salt=None)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def token(test_user):
    return _create_token(test_user.id, test_user.email)


@pytest.fixture(scope="function")
def client(db_session, test_user, token):
    app.dependency_overrides[get_db] = lambda: db_session

    async def _mock_user():
        return test_user

    app.dependency_overrides[get_current_user] = _mock_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
