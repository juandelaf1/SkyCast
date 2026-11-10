# SkyCast — Technical Case Study

## Problem
Integrating weather/climate context into downstream workflows (e.g. routing or observation validation) requires **stable, explicit API contracts**, traceable provenance, and operational safeguards (auth/rate limiting/observability) without coupling consumers to provider-specific quirks.

## Decisions
- **Contract-first endpoints:** expose versioned contracts for `POST /api/v1/route-weather` and `POST /api/v1/validate-observation`, with health/readiness and OpenAPI documentation.
- **Validation and explicit errors:** Pydantic request/response models and proper `422` validation errors for malformed payloads.
- **Configurable operational controls:** optional m2m auth/scopes, rate limiting (in-memory by default, Redis optional), correlation IDs, audit hooks, CORS and security headers.
- **Provider integration with provenance:** combine/normalize provider data (e.g. AEMET when applicable/configured, fallback strategies) and return provenance/estimation context in responses.
- **Reproducible schema evolution:** Alembic baseline migration and migration-aware initialization flow (`init_db`/`alembic upgrade head`, stamp for pre-existing DBs).
- **Evidence over claims:** commit reproducible contract/ops artifacts (`docs/visualizations/`, `scripts/smoke_export.py`) and contract-focused tests (success/validation/401/403).

## Trade-offs
- **Simplicity vs distribution:** in-memory rate limiting is simple but not distributed without Redis; Redis is supported as an optional backend.
- **Coverage vs determinism:** external providers introduce variability; tests/evidence use mocks/fakes to keep verification deterministic and offline.
- **Baseline migration strategy:** initial migration bootstraps schema from metadata for reproducibility; teams with legacy DBs must `stamp head` appropriately.
- **Scope:** periodic/ETL-style processing and provider availability constraints apply; not positioned as a guaranteed streaming system.

## Evidence
- **Contract tests:** `tests/test_api/test_contracts.py`, `tests/test_contract_health.py`, `tests/test_m2m.py` (and related API tests) validate shapes, validation errors, and auth/error behavior.
- **Operational/contract artifacts:** `docs/visualizations/api/*` and `docs/visualizations/ops/*` (samples, 401/403/429 examples, `openapi.json`, health/ready) generated via `python scripts/smoke_export.py`.
- **Schema/migrations:** `alembic/` baseline and `docs/db-schema.md`.
- **CI:** `.github/workflows/ci.yml`.

## Limits & learnings
- **Limits:** depends on provider configuration/availability and environment (DB/Redis/secrets); rate limiting semantics differ by backend; dashboard `/docs` UI captures remain manual.
- **Learnings:** making contracts, provenance, and error semantics explicit (and testable) reduces integration risk; versioned migrations and committed evidence improve maintainability and reviewability for portfolio/production evolution.
