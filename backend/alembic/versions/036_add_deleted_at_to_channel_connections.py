"""Add missing deleted_at columns to tables that filter by it.

The SQLAlchemy models and repositories reference deleted_at for soft-delete
filtering, but the column was never created in the database — causing a
ProgrammingError on any query that touches it.

Affected tables: channel_connections, assets, offer_gallery_images, avatars.

Revision ID: 036_add_deleted_at_channel_connections
Revises: 3fe863b5be0f
"""

from alembic import op

revision = "036_add_deleted_at_channel_connections"
down_revision = "3fe863b5be0f"
branch_labels = None
depends_on = None


def upgrade():
    # channel_connections — actively breaking Growth Studio dashboard
    op.execute("""
        ALTER TABLE channel_connections
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_channel_connections_deleted_at
        ON channel_connections (deleted_at);
    """)

    # assets — repository filters by deleted_at
    op.execute("""
        ALTER TABLE assets
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_assets_deleted_at
        ON assets (deleted_at);
    """)

    # offer_gallery_images — may not exist yet; guard with DO block
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'offer_gallery_images'
            ) THEN
                ALTER TABLE offer_gallery_images
                ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
                CREATE INDEX IF NOT EXISTS ix_offer_gallery_images_deleted_at
                ON offer_gallery_images (deleted_at);
            END IF;
        END; $$;
    """)

    # avatars — repository filters by deleted_at
    op.execute("""
        ALTER TABLE avatars
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_avatars_deleted_at
        ON avatars (deleted_at);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_channel_connections_deleted_at;")
    op.execute("ALTER TABLE channel_connections DROP COLUMN IF EXISTS deleted_at;")

    op.execute("DROP INDEX IF EXISTS ix_assets_deleted_at;")
    op.execute("ALTER TABLE assets DROP COLUMN IF EXISTS deleted_at;")

    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'offer_gallery_images'
            ) THEN
                DROP INDEX IF EXISTS ix_offer_gallery_images_deleted_at;
                ALTER TABLE offer_gallery_images DROP COLUMN IF EXISTS deleted_at;
            END IF;
        END; $$;
    """)

    op.execute("DROP INDEX IF EXISTS ix_avatars_deleted_at;")
    op.execute("ALTER TABLE avatars DROP COLUMN IF EXISTS deleted_at;")
