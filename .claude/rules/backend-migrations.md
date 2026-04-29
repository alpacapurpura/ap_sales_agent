---
globs: "backend/alembic/versions/**/*.py"
description: Idempotent Alembic migrations
---

# Migrations

All migrations MUST be idempotent. Raw SQL `IF NOT EXISTS`.

## Patterns
```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
# Enums: reference existing types en raw SQL. NUNCA sa.Enum()/postgresql.ENUM() dentro op.create_table()
```

## Prohibido
`op.create_table()` / `op.add_column()` / `op.create_index()` (no idempotentes). `sa.Enum(..., create_type=True)` (broken SA 2.0.27).

## Test antes prod (clone DB)
```bash
docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic stamp <PROD_REV> && POSTGRES_DB=migration_test alembic upgrade head'
docker exec -t visionarias_postgres psql -U postgres -c "DROP DATABASE migration_test;"
```
