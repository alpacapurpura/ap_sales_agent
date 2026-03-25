# Nicolify

**Context:** Multitenant SaaS (AaaS) automating marketing/sales for creators.
**Stack:** FastAPI (Async/SQLAlchemy 2.0), Next.js 15 (App Router/FSD), Clerk (Auth), Qdrant (RAG).
**Pattern:** Modular Monolith (DDD) + Docker-First.

## Core Domains (if you are unsure about the domain, refer to the `docs/domains/INDEX.md` file)

| Studio | Purpose | Modules |
| :--- | :--- | :--- |
| **Brand/Offer** | Identity capture & Offer Ladder builder | `brand`, `offer` |
| **Assets** | Auto-gen Landing Pages/Copies | `landing`, `assets` |
| **Growth** | Funnel diagram & Analytics | `analytics`, `advertising` |
| **Sales** | AI SDR (chat/close/schedule) & Ops Hub | `sales_agent`, `scheduling` |
| **Config** | External integrations (Meta, Shopify, etc.) | `connections` |

## Dev Environment (Docker-First)

**CRITICAL: Always run in Docker. Do not assume local exec works.**

- **Up (Dev):** `docker compose up -d`
- **Shell (Back):** `docker exec -it visionarias_brain_dev bash`
- **Shell (Front):** `docker exec -it visionarias_client_dev bash`
- **Db Migration:** `docker exec -it visionarias_brain_dev alembic upgrade head`
- **Tests/Lint:** `pytest`, `ruff check src --fix` (inside container)

## Migrations (Alembic)

**CRITICAL: Always write idempotent migrations.** Use raw SQL with `IF NOT EXISTS` instead of `op.create_table`/`op.add_column` — SQLAlchemy 2.0.27 ignores `create_type=False` on enums inside `op.create_table`.

- `CREATE TABLE IF NOT EXISTS` instead of `op.create_table()`
- `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` instead of `op.add_column()`
- `CREATE INDEX IF NOT EXISTS` instead of `op.create_index()`
- Enums: reference existing types directly in raw SQL, never use `sa.Enum`/`postgresql.ENUM` in `create_table`

**Test migrations before pushing to prod:**
```bash
# 1. Create test DB cloning current schema
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
# 2. Stamp at production revision (check prod error logs for current rev)
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REVISION>'
# 3. Run upgrade — must pass cleanly
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
# 4. Cleanup
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```

## Critical Constraints

1.  **Anti-Hallucination:** Read `docs/domains/INDEX.md` before coding. Never guess classes/fields.
2.  **Tenant Isolation:** ALL queries must filter by `X-Tenant-ID`. No data leaks.
3.  **Architecture:**
    *   **Backend:** `domain` -> `infrastructure` -> `application` -> `api`.
    *   **Frontend:** FSD (`shared` -> `entities` -> `features` -> `widgets` -> `pages`). No deep imports.
4.  **Data:** Soft deletes only (`deleted_at`). SQLAlchemy 2.0 syntax (`select(Model)`).
5.  **UX:** AI-first. Auto-fill buttons, guided flows.

## Copilot Resilience Rules
- NEVER hardcode field names in copilot tools — use Pydantic model introspection (`schema_introspection.py`)
- New modules: add `ModuleDescriptor` to `copilot/domain/module_registry.py`
- New routes: update `navigation_map.py` + `tools/registry.py` ROUTE_TOOL_MAP
- New fields/sections in existing models: NO copilot changes needed (auto-discovered via `model_fields`)
- Tools use `MODULE_REGISTRY` for data access, not direct repo imports
- Route-based tool selection in `tools/registry.py` — only relevant tools are bound per route

## Product Vision
- If you need to take a decision and need to know about the product vision: `docs/vision/product-vision.md`.
