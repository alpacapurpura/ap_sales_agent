"""copilot: +pg_trgm extension + GIN indices for ask_tenant_data fuzzy match (F5)

Revision ID: 070_pg_trgm_indices
Revises: 069_copilot_inspiration
Create Date: 2026-04-25

F5 deliverable. Enables Postgres trigram similarity for offer + conversation
fuzzy entity resolution inside the ask_tenant_data subgraph (entity_resolver
node). Without GIN trigram indices a `similarity(name, query) > 0.3` filter
falls back to seq scan on every product/conversation table.

`CREATE EXTENSION IF NOT EXISTS pg_trgm` requires the postgres role to have
extension privilege. In all Nicolify envs (local + Visionarias prod) the
default role owns the database — extension creation succeeds. If a future
tenant runs Postgres with restricted role, manual `CREATE EXTENSION` ahead of
time is required (no DO-block fallback because silent-degrade would mask the
fact that fuzzy match fell back to seq scan in prod).

refs: docs/domains/copilot/redesign-2026-04/02-architecture-target.md §6
      docs/domains/copilot/redesign-2026-04/phases/F5-ask-tenant-data.md
"""

from collections.abc import Sequence

from alembic import op

revision: str = "070_pg_trgm_indices"
down_revision: str | None = "069_copilot_inspiration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Idempotent extension + GIN indices per .claude/rules/backend-migrations.md."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_name_trgm
        ON products USING gin (name gin_trgm_ops)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_conversations_title_trgm
        ON copilot_conversations USING gin (title gin_trgm_ops)
        WHERE title IS NOT NULL
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP. Indices + extension are additive; preserve on rollback."""
