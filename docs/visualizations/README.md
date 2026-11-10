# Visualizaciones y evidencias (registro)

Registro trazable de **evidencias operativas y de contrato** de SkyCast (API/operación). No incluye secretos, PII ni afirmaciones de producción no demostrada.

## Estructura
- `docs/visualizations/api/` — evidencias de contratos/respuestas (éxito y errores de contrato), p. ej. `route-weather`, `validate-observation`, ejemplos `401/403/429`.
- `docs/visualizations/ops/` — evidencias operativas (p. ej. `health`, `health/ready`, `openapi.json`).
- `docs/visualizations/dashboard/` — capturas manuales del dashboard/UI interno (con **datos seed/test**) cuando se generen.

## Artefactos generados (ejemplos)
- **API:** `route-weather.sample.json`, `validate-observation.sample.json`, `route-weather.error-401.json`, `route-weather.error-403.json`, `route-weather.error-429.json`
- **Ops:** `health.json`, `ready.json`, `openapi.json`

## Metadatos mínimos
- Fecha y commit
- `contract_version`/endpoint o componente
- Entorno/configuración relevante (m2m/redis on/off) **sin secretos**
- Comando o script de regeneración

## Regeneración (local, reproducible)
- Contratos y smoke (sin red externa, proveedores simulados):
  ```bash
  python scripts/smoke_export.py
  ```
  Genera/actualiza ejemplos en `docs/visualizations/api/` y `docs/visualizations/ops/` (incluye snapshot de `/openapi.json`).
- Documentación interactiva y capturas manuales:
  ```bash
  uvicorn app.main:app --reload
  ```
  Revisar `/docs` y `/openapi.json`; para dashboard/UI, usar **datos seed/test** y capturar con viewport/idioma consistentes (guardar en `docs/visualizations/dashboard/` con nota de fecha/commit/config).
- Tests de contrato/errores:
  ```bash
  python -m pytest tests/test_api/test_contracts.py
  ```

> Registrar solo evidencias representativas y regenerables; optimizar imágenes y evitar artefactos redundantes.

