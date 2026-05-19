from sqlalchemy.orm import Session
from app.db.models import Zona, Municipio, Estacion, FuenteDato, UmbralAlerta


def seed_initial_data(db: Session):
    if db.query(Zona).count() > 0:
        return

    zonas = [
        {"codigo": "centro", "nombre": "Centro", "es_default": True},
        {"codigo": "norte", "nombre": "Norte", "es_default": False},
        {"codigo": "sur", "nombre": "Sur", "es_default": False},
        {"codigo": "este", "nombre": "Este", "es_default": False},
        {"codigo": "oeste", "nombre": "Oeste", "es_default": False},
    ]
    for z in zonas:
        db.add(Zona(**z))
    db.commit()

    zonas_db = {z.codigo: z.id for z in db.query(Zona).all()}

    municipios = [
        {"nombre": "Madrid", "lat": 40.4168, "lon": -3.7038, "cod_ine": "28079", "zona_id": zonas_db["centro"]},
        {"nombre": "Alcalá de Henares", "lat": 40.4821, "lon": -3.3644, "cod_ine": "28005", "zona_id": zonas_db["este"]},
        {"nombre": "Móstoles", "lat": 40.3263, "lon": -3.8648, "cod_ine": "28092", "zona_id": zonas_db["sur"]},
        {"nombre": "Fuenlabrada", "lat": 40.2842, "lon": -3.7946, "cod_ine": "28049", "zona_id": zonas_db["sur"]},
        {"nombre": "Leganés", "lat": 40.3288, "lon": -3.7635, "cod_ine": "28074", "zona_id": zonas_db["sur"]},
        {"nombre": "Getafe", "lat": 40.3057, "lon": -3.7300, "cod_ine": "28065", "zona_id": zonas_db["sur"]},
        {"nombre": "Alcorcón", "lat": 40.3459, "lon": -3.8242, "cod_ine": "28013", "zona_id": zonas_db["sur"]},
        {"nombre": "Torrejón de Ardoz", "lat": 40.4538, "lon": -3.4697, "cod_ine": "28148", "zona_id": zonas_db["este"]},
        {"nombre": "Parla", "lat": 40.2362, "lon": -3.7675, "cod_ine": "28106", "zona_id": zonas_db["sur"]},
        {"nombre": "San Sebastián de los Reyes", "lat": 40.5449, "lon": -3.6258, "cod_ine": "28134", "zona_id": zonas_db["norte"]},
        {"nombre": "Rivas-Vaciamadrid", "lat": 40.3375, "lon": -3.6136, "cod_ine": "28124", "zona_id": zonas_db["sur"]},
        {"nombre": "Colmenar Viejo", "lat": 40.6591, "lon": -3.7636, "cod_ine": "28047", "zona_id": zonas_db["norte"]},
        {"nombre": "Tres Cantos", "lat": 40.6009, "lon": -3.7081, "cod_ine": "28151", "zona_id": zonas_db["norte"]},
        {"nombre": "Boadilla del Monte", "lat": 40.4054, "lon": -3.8784, "cod_ine": "28025", "zona_id": zonas_db["oeste"]},
        {"nombre": "Las Rozas de Madrid", "lat": 40.4929, "lon": -3.8737, "cod_ine": "28077", "zona_id": zonas_db["oeste"]},
    ]
    for m in municipios:
        db.add(Municipio(**m))
    db.commit()

    muni_by_name = {m.nombre: m for m in db.query(Municipio).all()}

    estaciones = [
        {"indicativo": "3195", "nombre": "Madrid-Retiro", "provincia": "Madrid", "lat": 40.4114, "lon": -3.6788, "municipio_id": muni_by_name.get("Madrid").id if muni_by_name.get("Madrid") else None},
        {"indicativo": "3129", "nombre": "Madrid-Golfo de Vizcaya", "provincia": "Madrid", "lat": 40.4064, "lon": -3.7111, "municipio_id": muni_by_name.get("Madrid").id if muni_by_name.get("Madrid") else None},
        {"indicativo": "3170", "nombre": "Alcalá de Henares", "provincia": "Madrid", "lat": 40.4833, "lon": -3.3667, "municipio_id": muni_by_name.get("Alcalá de Henares").id if muni_by_name.get("Alcalá de Henares") else None},
        {"indicativo": "3200", "nombre": "Getafe", "provincia": "Madrid", "lat": 40.2947, "lon": -3.7214, "municipio_id": muni_by_name.get("Getafe").id if muni_by_name.get("Getafe") else None},
        {"indicativo": "3266", "nombre": "Torrejón de Ardoz", "provincia": "Madrid", "lat": 40.4500, "lon": -3.4667, "municipio_id": muni_by_name.get("Torrejón de Ardoz").id if muni_by_name.get("Torrejón de Ardoz") else None},
    ]
    for e in estaciones:
        db.add(Estacion(**e))
    db.commit()

    fuentes = [
        {"codigo": "aemet", "nombre": "AEMET OpenData", "url": "https://opendata.aemet.es", "cobertura": "España"},
        {"codigo": "openweather", "nombre": "OpenWeatherMap", "url": "https://api.openweathermap.org", "cobertura": "Global"},
        {"codigo": "manual", "nombre": "Registro Manual", "url": None, "cobertura": "Usuario"},
    ]
    for f in fuentes:
        db.add(FuenteDato(**f))
    db.commit()

    umbrales = [
        {"variable": "temperatura", "nivel": "rojo", "valor": 40.0, "descripcion": "Calor extremo", "color_hex": "#DC2626", "icono": "🔥"},
        {"variable": "temperatura", "nivel": "naranja", "valor": 35.0, "descripcion": "Calor alto", "color_hex": "#EA580C", "icono": "🟠"},
        {"variable": "temperatura", "nivel": "amarillo", "valor": 30.0, "descripcion": "Calor moderado", "color_hex": "#FACC15", "icono": "🌡️"},
        {"variable": "temperatura", "nivel": "azul", "valor": 0.0, "descripcion": "Helada", "color_hex": "#2563EB", "icono": "❄️"},
        {"variable": "viento", "nivel": "rojo", "valor": 70.0, "descripcion": "Viento muy fuerte", "color_hex": "#DC2626", "icono": "💨"},
        {"variable": "viento", "nivel": "naranja", "valor": 50.0, "descripcion": "Viento fuerte", "color_hex": "#EA580C", "icono": "💨"},
        {"variable": "lluvia", "nivel": "rojo", "valor": 30.0, "descripcion": "Lluvia intensa", "color_hex": "#DC2626", "icono": "🌧️"},
        {"variable": "lluvia", "nivel": "naranja", "valor": 15.0, "descripcion": "Lluvia moderada", "color_hex": "#EA580C", "icono": "🌧️"},
        {"variable": "humedad", "nivel": "rojo", "valor": 90.0, "descripcion": "Humedad muy alta", "color_hex": "#DC2626", "icono": "💧"},
        {"variable": "humedad", "nivel": "naranja", "valor": 80.0, "descripcion": "Humedad alta", "color_hex": "#EA580C", "icono": "💧"},
    ]
    for u in umbrales:
        db.add(UmbralAlerta(**u))
    db.commit()

    print("Datos iniciales sembrados.")