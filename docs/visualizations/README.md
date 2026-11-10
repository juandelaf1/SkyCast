# Visualizaciones y evidencias (registro)

Registro trazable de **evidencias operativas y de contrato** de SkyCast (API/operación). No incluye secretos, PII ni afirmaciones de producción no demostrada.

## Estructura
- `docs/visualizations/api/` — evidencias de contratos OpenAPI/respuestas (p. ej. ejemplos JSON de `route-weather`, `validate-observation`, captura de `/docs`).
- `docs/visualizations/ops/` — evidencias operativas (p. ej. `health`, `health/ready`, smoke results).
- `docs/visualizations/dashboard/` — capturas del dashboard interno si aplica (con datos seed/test).

## Metadatos mínimos
- Fecha y commit
- `contract_version`/endpoint o componente
- Entorno/configuración relevante (m2m/redis on/off) **sin secretos**
- Comando o script de regeneración

## Regeneración (local, reproducible)
- Contratos y smoke (sin red externa, proveedores simulados): `python scripts/smoke_export.py` → genera/actualiza ejemplos en `docs/visualizations/api/` y `docs/visualizations/ops/`.
- Documentación interactiva: `uvicorn app.main:app --reload` y revisar `/docs`, `/openapi.json` (capturas manuales con viewport fijo si se añaden).
- Tests de contrato: `python -m pytest tests/test_api/test_contracts.py`.

> Registrar solo evidencias representativas y regenerables; optimizar imágenes y evitar artefactos redundantes.
