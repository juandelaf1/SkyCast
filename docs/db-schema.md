# Esquema de base de datos (estado actual)

## Fuente de verdad
- **Modelos ORM:** `app/db/models/` (SQLAlchemy) y `app/db/base.py`.
- **Inicialización actual:** `init_db()` en `app/db/__init__.py` ejecuta `Base.metadata.create_all(bind=engine)` y aplica seed inicial (`app/db/seed.py`). No hay carpeta de migraciones versionadas (p. ej. Alembic) en el estado actual.

## Tablas/modelos principales (referencia)
`Alerta`, `Estacion`, `FuenteDato`, `Medicion`, `Municipio`, `UmbralAlerta`, `Usuario`, `Zona` (ver `app/db/models/` para columnas, tipos y relaciones).

## Camino de migración recomendado (evolución segura)
- Para cambios de esquema futuros, introducir **migraciones versionadas** (recomendado: Alembic) con una migración inicial que refleje el estado actual.
- Mantener `init_db`/`create_all` solo para entornos de bootstrap/test compatibles, o migrar la creación a `alembic upgrade head` según estrategia de despliegue.
- Todo cambio de esquema debe ir acompañado de pruebas y actualización de esta documentación.

## Regeneración de referencia (opcional)
Es posible generar un DDL de referencia desde los metadatos ORM para documentación (sin sustituir migraciones). Ejemplo conceptual:
```python
from sqlalchemy.schema import CreateTable
from app.db.base import Base
# imprimir CreateTable para cada tabla en Base.metadata.sorted_tables
```
