# Esquema de base de datos y migraciones

## Fuente de verdad
- **Modelos ORM:** `app/db/models/` (SQLAlchemy) y `app/db/base.py`.
- **Migraciones versionadas:** `alembic/` (`alembic.ini`, `alembic/env.py`, `alembic/versions/`).
- **Migración inicial (baseline):** `alembic/versions/76df699665bd_initial_schema.py` crea el esquema actual desde metadata.

## Flujo reproducible (recomendado)
1. Configurar `DATABASE_URL` (por defecto SQLite en `settings`).
2. Aplicar migraciones:
   ```bash
   alembic upgrade head
   ```
3. Inicializar datos seed cuando corresponda:
   ```bash
   python -m app.db
   ```
   `init_db()` intenta aplicar migraciones Alembic si están disponibles y luego ejecuta seed idempotente.

### Bases existentes creadas con `create_all`
Si la base ya tiene tablas pero no `alembic_version`, marcar baseline sin recrear:
```bash
alembic stamp head
```
`init_db()` también intenta detectar este caso y estampar `head` antes de continuar.

## Tablas/modelos principales (referencia)
`Alerta`, `Estacion`, `FuenteDato`, `Medicion`, `Municipio`, `UmbralAlerta`, `Usuario`, `Zona` (ver `app/db/models/` para columnas, tipos y relaciones).

## Evolución de esquema
- Crear migraciones para cada cambio: `alembic revision -m "descripcion"` (o `--autogenerate` con revisión manual).
- Revisar y probar migraciones (`upgrade`/`downgrade`) antes de integrar.
- Mantener compatibilidad con bootstrap/tests; evitar cambios destructivos no documentados.
- Actualizar esta documentación y pruebas/contratos afectados.

