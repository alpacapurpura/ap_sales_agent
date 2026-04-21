---
globs: "backend/alembic/versions/**/*.py"
description: Idempotent Alembic migration rules
---

# Migration Rules

**All migrations MUST be idempotent.** Raw SQL con `IF NOT EXISTS`.

## Required Patterns
```python
# Tables
op.execute("CREATE TABLE IF NOT EXISTS ...")

# Columns
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")

# Indexes
op.execute("CREATE INDEX IF NOT EXISTS ...")

# Enums
# Reference existing types en raw SQL. NEVER `sa.Enum()` / `postgresql.ENUM()` dentro `op.create_table()`
```

## Forbidden
- `op.create_table()` — no idempotent
- `op.add_column()` — no idempotent
- `op.create_index()` — no idempotent
- `sa.Enum(..., create_type=True)` — broken SA 2.0.27

## Test Before Prod
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REV>'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
