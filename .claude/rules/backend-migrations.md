---
globs: "backend/alembic/versions/**/*.py"
description: Idempotent Alembic migration rules
---

# Migration Rules

**CRITICAL: All migrations MUST be idempotent.** Use raw SQL with `IF NOT EXISTS`.

## Required Patterns
```python
# Tables
op.execute("CREATE TABLE IF NOT EXISTS ...")

# Columns
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")

# Indexes
op.execute("CREATE INDEX IF NOT EXISTS ...")

# Enums
# Reference existing types in raw SQL. NEVER use sa.Enum() or postgresql.ENUM() inside op.create_table()
```

## Forbidden Patterns
- `op.create_table()` — not idempotent
- `op.add_column()` — not idempotent
- `op.create_index()` — not idempotent
- `sa.Enum(..., create_type=True)` — broken in SA 2.0.27

## Test Before Prod
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REV>'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
