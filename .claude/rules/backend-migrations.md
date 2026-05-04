---
globs: "backend/alembic/versions/**/*.py"
description: Idempotent Alembic migrations
---

# Migrations

Idempotentes. Raw SQL `IF NOT EXISTS`.

## Patterns
```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
# Enums: raw SQL ref existing types. NUNCA sa.Enum()/postgresql.ENUM() en op.create_table()
```

## Prohibido
`op.create_table()`/`add_column()`/`create_index()` (no idempotentes). `sa.Enum(..., create_type=True)` (broken SA 2.0.27).

## Test pre-prod
Clone DB workflow → `docs/domains/migrations.md`. Steps: create migration_test DB · pg_dump schema · stamp prod rev · upgrade head · drop.
