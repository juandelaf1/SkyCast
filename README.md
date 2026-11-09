# SkyCast

API y servicios de inteligencia climática (FastAPI) orientados a **integración por contratos** (p. ej. logística/EnRuta) y monitorización periódica.

[Case study / portfolio](https://juandelaf1.github.io/projects/sky-cast) *(puede describir una versión anterior; este README refleja el estado verificado del repositorio).*

## Estado actual (verificado)

- **Contratos de integración (v1):** `POST /api/v1/route-weather` (clima por waypoints/ruta; preferencia AEMET en España con fallback Open-Meteo) y `POST /api/v1/validate` (validación de riesgo por ruta/actividad). Respuestas con `contract_version` y procedencia (`fuentes`, `data_quality`, estado fallback) según implementación.
- **Operación:** `GET /api/v1/health`, `GET /api/v1/health/ready`, `GET /api/v1/health/capabilities`. OpenAPI snapshot en `docs/openapi.snapshot.json`.
- **Seguridad/ops (integración m2m):** API key opcional con scopes en contratos (`tools.opencode`/m2m según config), rate limit (in-memory por defecto; **opcional Redis** con `REDIS_URL`), auditoría estructurada y JSONL opcional (`SKYCAST_AUDIT_FILE`), `X-Correlation-Id`, CORS configurable, headers de seguridad + HSTS opcional (`SKYCAST_HSTS`/entorno).
- **Stack base:** Python, FastAPI, validación Pydantic; ingestas/ETL y visualización (Streamlit/PostgreSQL) según módulos presentes. CI y Docker según workflows/compose del repo.

## Limitaciones (honestas)

- Monitorización **periódica/ETL** según configuración; no streaming en tiempo real garantizado.
- Disponibilidad/calidad dependiente de proveedores externos (AEMET/Open-Meteo, etc.) y de credenciales/configuración (`AEMET_API_KEY` en entorno, nunca commitear).
- Rate limit in-memory no es distribuido sin `REDIS_URL` + backend Redis; auditoría central/rotación y secretos gestionados son escalables a posterior según infraestructura.
- Algunas capacidades descritas en material histórico/portfolio pueden diferir del estado actual del código; verificar contra endpoints/tests/workflows.

## Uso rápido (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# Docs: http://127.0.0.1:8000/docs
```

Plantilla de producción: `docker-compose.prod.yml`. Ver `DECISION_LOG.md`/docs de operación en el workspace para backlog escalable.

## Autoría

**Juan de la Fuente** — [@juandelaf1](https://github.com/juandelaf1)
