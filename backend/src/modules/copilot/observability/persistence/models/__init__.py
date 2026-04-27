"""SQLAlchemy ORM models for the observability module.

Models are co-located with the persistence layer (repositories) to keep
the observability module self-contained — nothing here leaks back into
``copilot.infrastructure.models``.

Generated columns (``occurred_on``, ``occurred_year_month``) declared in
migration 075 are intentionally **not** mapped on the ORM side: their
expressions use Postgres-specific operators that SQLite (used in unit
tests via ``Base.metadata.create_all``) cannot evaluate. Reports and the
materialized view (Phase 3) read those columns via raw SQL.
"""
