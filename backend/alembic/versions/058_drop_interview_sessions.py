"""Drop interview_sessions table — replaced by guided_mode on copilot_conversations.

The interview engine (domain/interview_configs, interview_session model, service,
repository, API endpoints) has been consolidated into the main Copilot chat
surface. Guided-setup state now lives inside
``copilot_conversations.procedure_state`` JSONB under the ``"guided"`` key, so
no extra column is needed.

Idempotent: uses ``DROP TABLE IF EXISTS`` so re-running or applying on a fresh
schema (where the table never existed) is safe.

Revision ID: 058_drop_interview_sessions
Revises: 057_asset_scope_purpose
Create Date: 2026-04-22 18:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "058_drop_interview_sessions"
down_revision: str | None = "057_asset_scope_purpose"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop interview_sessions table + stale FK column on buyer_personas. Idempotent."""
    op.execute("DROP TABLE IF EXISTS interview_sessions CASCADE")
    # The buyer_personas row used to carry a pointer to the interview that
    # created it. With the table gone the column is dead weight; drop it.
    op.execute("ALTER TABLE buyer_personas DROP COLUMN IF EXISTS interview_session_id")


def downgrade() -> None:
    """Re-create a minimal interview_sessions shell if rollback is required.

    The original schema lived in migration 044 + hardening; we re-materialise
    only the skeleton so a downgrade does not leave dangling foreign keys.
    Full data reconstruction is not supported — the interview engine has been
    deleted from the codebase.
    """
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            domain VARCHAR(64) NOT NULL,
            config_snapshot JSONB NOT NULL,
            conversation_id UUID,
            mapa_global JSONB NOT NULL DEFAULT '{}'::jsonb,
            bloque_actual VARCHAR(64) NOT NULL,
            bloques_completados JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(32) NOT NULL,
            messages_count INTEGER NOT NULL DEFAULT 0,
            entity_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        "ALTER TABLE buyer_personas ADD COLUMN IF NOT EXISTS interview_session_id UUID",
    )
