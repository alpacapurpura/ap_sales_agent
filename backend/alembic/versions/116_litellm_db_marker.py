"""LiteLLM Proxy: separate Postgres database creation marker.

S3 PR-2 PI-2. Crea DB ``visionarias_litellm_db`` separada del schema
Nicolify (``visionarias_logs``). LiteLLM Proxy ejecuta sus propias Prisma
migrations en startup contra esta DB. Nicolify Alembic NO ownership de
tablas ``LiteLLM_*``.

Idempotente: ``CREATE DATABASE IF NOT EXISTS`` equivalente via try/except on
DuplicateDatabase (Postgres does not support IF NOT EXISTS for DATABASE).

Revision ID: 116_litellm_db_marker
Revises: 115_routing_log_tier_to_role
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

revision: str = "116_litellm_db_marker"
down_revision: str | None = "115_routing_log_tier_to_role"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Create separate database for LiteLLM Proxy."""
    # NOTE: CREATE DATABASE cannot execute inside a transaction block.
    # Alembic auto-wraps in a transaction → must commit first + use isolation level.
    # Workaround: commit the active transaction, then issue CREATE DATABASE.
    #
    # Idempotente: catch DuplicateDatabaseError (psycopg2.errors.DuplicateDatabase).
    op.execute("COMMIT")  # release alembic transaction
    try:
        op.execute("CREATE DATABASE visionarias_litellm_db")
    except Exception as e:
        # Already exists OR user lacks privilege — log + continue.
        # Production: privilege should be granted via init.sql.
        if "already exists" not in str(e).lower():
            raise


def downgrade() -> None:
    """No-op. Dropping LiteLLM DB destroys virtual keys + spend logs."""
    # Explicit no-op por safety. Si requerido manual:
    # docker exec visionarias_postgres psql -U postgres -c "DROP DATABASE visionarias_litellm_db"
