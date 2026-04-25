"""copilot: +copilot_conversations.workflow_state JSONB column (F6)

Revision ID: 071_copilot_workflow_state
Revises: 070_pg_trgm_indices
Create Date: 2026-04-25

F6 deliverable. Adds the unified ``workflow_state`` JSONB column that the
``WorkflowExecutionState`` payload lives in (declarative engine in
``copilot/application/workflows/engine.py``). Coexists with the legacy
``procedure_state`` column during the cutover — readers can fall back to
``procedure_state`` for conversations that started before F6 (see
``ConversationRepository.get_workflow_state(..., fallback_to_procedure=True)``).

Migration is idempotent (raw ``ADD COLUMN IF NOT EXISTS``). The backfill
step copies live ``procedure_state`` payloads into ``workflow_state`` so
the new readers see the same data without forcing a code-side dual read for
every accessor in the codebase. ``procedure_state`` is **NOT dropped** here
— that lives in F-pos cutover after we are sure no consumer reads it.

refs:
- docs/domains/copilot/redesign-2026-04/02-architecture-target.md §3
- docs/domains/copilot/redesign-2026-04/phases/F6-workflow-unification.md
- .claude/rules/backend-migrations.md (idempotent + no DROP during cutover)
"""

from collections.abc import Sequence

from alembic import op

revision: str = "071_copilot_workflow_state"
down_revision: str | None = "070_pg_trgm_indices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``workflow_state`` JSONB + backfill from ``procedure_state``.

    Idempotent per .claude/rules/backend-migrations.md — re-running upgrade
    is a no-op once the column exists. Backfill only writes rows whose
    ``workflow_state`` is still NULL, so a partial re-run is safe.
    """
    op.execute(
        """
        ALTER TABLE copilot_conversations
        ADD COLUMN IF NOT EXISTS workflow_state JSONB
        """,
    )
    op.execute(
        """
        UPDATE copilot_conversations
        SET workflow_state = procedure_state
        WHERE workflow_state IS NULL
          AND procedure_state IS NOT NULL
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP — dropping ``workflow_state`` would lose live state.

    Cutover (F-pos) will eventually drop ``procedure_state`` instead in a
    separate idempotent migration once code stops reading it.
    """
