# SkyCast — Enterprise Climate Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue?logo=docker)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-158%20passing-brightgreen)](https://pytest.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/juandelaf1/SkyCast/ci.yml?branch=portfolio-analisis&label=CI&logo=github)](https://github.com/juandelaf1/SkyCast/actions)

Plataforma de monitorización climática con datos oficiales de AEMET, crowdsourcing colaborativo (modelo Waze), y alertas inteligentes. Diseñada como núcleo de datos para integrarse en plataformas logísticas empresariales.

---

## Problema

Las apps del tiempo generales no cubren necesidades específicas:

- Un **ayuntamiento** necesita saber si mañana habrá viento > 50 km/h para cerrar parques, no solo "23°C y soleado".
- Una **empresa logística** necesita decidir si retrasa flotas por lluvia intensa en una ruta concreta.
- Un **técnico municipal** cruza datos de sensores oficiales con reportes manuales de ciudadanos para decidir si activa un protocolo de heladas.

SkyCast resuelve esto combinando **datos oficiales** (AEMET OpenData), **crowdsourcing** (reportes manuales con validación geoespacial), y **analytics** (alertas, anomalías, tendencias históricas).

## Diferencial

| Diferencia | Apps del tiempo | SkyCast |
|------------|----------------|---------|
| Fuente principal | API privada | AEMET OpenData (oficial España) |
| Crowdsourcing | No | Reportes manuales con geovalidación |
| Alertas por umbral fijo | Genéricas | Configurables por usuario |
| Histórico analizable | Limitado | CRUD completo + ETL con linaje |
| API para terceros | No | REST documentada (Swagger) |
| Destinado a | Consumidor final | Empresas, ayuntamientos, logística |

## Arquitectura

```
FastAPI + Pydantic ── REST API ──┐
                                  ├── PostgreSQL (SQLAlchemy ORM)
Streamlit + Plotly ─── Dashboard ─┘
                                  │
APScheduler ─── AEMET API ────────┘
    (cada 2h, fallback OpenWeatherMap)
```

### Flujo ETL (traza completa)

```
Extraer (AEMET JSON) → Transformar (Pandas: nulos, duplicados, tipos)
                      → Cargar (SQLAlchemy) → LineageLogger (traza)
```

Cada paso registra filas entrada/salida/descartadas con `LineageLogger`.

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| API | FastAPI + Uvicorn + Pydantic + async |
| Base de datos | PostgreSQL 16 / SQLite + SQLAlchemy ORM (9 modelos) |
| Dashboard | Streamlit + Plotly + Geopandas + Folium |
| ETL | Pandas + NumPy + LineageLogger |
| Autenticación | JWT + SHA-256 + salt único |
| Cache | Redis (opcional, fallback in-memory) |
| Scheduling | APScheduler (fetch AEMET cada 2h) |
| Contenedores | Docker + Docker Compose |
| CI/CD | GitHub Actions (pytest + ruff + Docker build) |
| Tests | 158 tests, pytest + httpx, pre-push hooks |

## Inicio rápido

```bash
git clone https://github.com/juandelaf1/SkyCast.git
cd SkyCast
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Añadir AEMET_API_KEY
python -m app.db       # Inicializar BD
uvicorn app.main:app --reload --port 8000
streamlit run app/dashboard/app.py --server.port 8501
```

Docs: http://localhost:8000/docs | Dashboard: http://localhost:8501

## API endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Registro |
| POST | `/api/v1/auth/login` | Login JWT |
| GET | `/api/v1/clima?lat=&lon=` | Clima actual |
| GET | `/api/v1/geo/{ciudad}` | Geocodificar |
| GET | `/api/v1/registros?page=&limit=` | Histórico paginado |
| POST | `/api/v1/registros` | Reporte manual (crowdsourcing) |
| POST | `/api/v1/comparar` | Manual vs AEMET |
| GET/POST | `/api/v1/alertas` | Umbrales configurables |

## Seguridad

- Contraseñas: SHA-256 + salt (16 bytes) por usuario
- Tokens: JWT HS256, expiración 24h
- Validación: Pydantic + rangos físicos (-20/60°C, 0-100% humedad)
- Rate limiting: slowapi (30 req/min clima, 10 geo)
- Pre-push hooks: lint + tests + anti-leak secrets

## Calidad (158 tests, 0 failures, CI/CD)

```bash
pytest --cov=app --cov-report=html   # 158 tests, 33 files
ruff check app/ tests/               # 0 errores
```

Cobertura: API endpoints, auth, alerts, validators, ETL (extract/transform/load), haversine, anomaly detection, cache, lineage logger, servicios externos mockeados.

## Visión: plataforma logística

SkyCast está diseñado como **módulo climático** de una plataforma logística mayor. Los endpoints REST permiten que sistemas de routing, flotas, y seguros consuman datos climáticos históricos y en tiempo real sin acoplamiento. Próximos pasos naturales:

1. Alertas push (email/Telegram) para umbrales personalizados
2. Geo-cercas: disparar alertas cuando una ubicación supere umbrales
3. Integración con APIs de routing (calcular retrasos por clima)
4. Modelo predictivo (regresión temp/humedad a 48h)

---

## Evolución del proyecto

| Fase | Proyecto | Stack | Hito |
|------|----------|-------|------|
| F1 | [SkyCast V1](https://github.com/juandelaf1/SkyCast-V1) | Streamlit + CSV | Prototipo funcional |
| F2 | [ClimApp](https://github.com/juandelaf1/ClimApp) | Flask MVC + AEMET | Arquitectura por capas, 66 tests |
| F3 | [Vortex](https://github.com/juandelaf1/Vortex) | FastAPI/Flask + PostgreSQL | ETL, linaje, trazabilidad |
| F4-Pre | [SkyCast V2 Pre](https://github.com/juandelaf1/SkyCast-V2-Pre) | FastAPI + Docker | JWT con salt, anomalías |
| **F4** | **SkyCast** | **FastAPI + PostgreSQL + Docker** | **158 tests, CI/CD, producción** |

---

## Autor

**Juan de la Fuente** — [@juandelaf1](https://github.com/juandelaf1)

MIT © 2026
