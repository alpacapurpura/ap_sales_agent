"""copilot multimodal: blocks-capable message shape (no schema change).

Adds a COMMENT on copilot_conversations.messages to document the v2 block shape,
and a partial GIN index for quickly locating conversations that already have blocks.

No column-level change needed — messages is JSONB; the element shape change is
forward-compat. Legacy v1 readers see unchanged role+content; v2 readers prefer
blocks when present (read adapter in message_codec.py).

Revision ID: 056_copilot_multimodal
Revises: 055_copilot_refactor_v2
Create Date: 2026-04-22 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "056_copilot_multimodal"
down_revision: str | None = "055_copilot_refactor_v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Marker revision: document v2 message shape + add blocks GIN index (idempotent)."""
    # Document the v2 shape change (no actual schema change — JSONB is schema-free).
    op.execute("""
        COMMENT ON COLUMN copilot_conversations.messages IS
        'JSONB array of Message objects. Shape v2 (2026-04-22):
         { id, role, content, blocks?, status, created_at, tool_calls?,
           tool_call_id?, name?, tokens_used?, metadata? }.
         Legacy v1 readers treat missing fields as null.
         Read adapter: message_codec.decode_message() handles both shapes.'
    """)

    # Partial GIN index for counting / locating conversations that carry block arrays.
    # Useful for migration monitoring (how many convs have been enriched with blocks).
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_has_blocks
          ON copilot_conversations ((messages::jsonb @? '$[*].blocks'))
          WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    """Remove the GIN index (COMMENT removal is optional / informational)."""
    op.execute("DROP INDEX IF EXISTS ix_copilot_conv_has_blocks")
