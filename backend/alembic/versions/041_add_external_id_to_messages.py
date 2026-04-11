"""add external_id to messages

Revision ID: 041_add_external_id_to_messages
Revises: 040_add_archived_deleted_products
Create Date: 2026-04-11

The `MessageModel` ORM has declared `external_id` (channel message id, e.g.
ManyChat) for a while, but no migration ever added the column to the DB. Any
SELECT from the model crashed with `UndefinedColumn: messages.external_id`,
which broke `GET /api/v1/closer-studio/conversations/{lead_id}` and made the
inbox show "Conversación no encontrada" for every existing conversation.

Idempotent raw SQL — safe to re-run.
"""

from alembic import op

revision = "041_add_external_id_to_messages"
down_revision = "040_add_archived_deleted_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'messages'
            ) THEN
                ALTER TABLE messages
                ADD COLUMN IF NOT EXISTS external_id VARCHAR NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'messages'
            ) THEN
                ALTER TABLE messages DROP COLUMN IF EXISTS external_id;
            END IF;
        END $$;
    """)
