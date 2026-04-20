"""create social_proof tables and seed from legacy brand_settings JSONB

Migration 054 — social_proof bounded context.

Creates four tables:
  * ``testimonials``
  * ``authority_items``
  * ``team_members``
  * ``social_proof_placements``

Then backfills rows from the legacy JSONB arrays stored under
``tenants.config_json['brand_settings']['{testimonials,authority_vault,team}']``
(and the nested ``team.key_leadership`` list), creating one default
placement ``brand_homepage`` per seeded row.

Idempotency:
  * All DDL uses ``IF NOT EXISTS`` / ``IF NOT EXISTS`` indexes.
  * The backfill matches rows by ``(tenant_id, source)`` and inserts with
    ``ON CONFLICT DO NOTHING`` on the partial unique index for placements,
    and guards the source-row upsert with a ``NOT EXISTS`` check keyed on
    ``(tenant_id, legacy_id)`` stored in ``tags`` / ``context`` so re-runs
    are safe even on a partially-migrated DB.

Downgrade:
  Drops the four tables. Since the legacy JSONB blob is kept intact during
  phase 1, no data is lost — the cleanup of the JSONB happens in a later
  migration once the app has fully switched over to the tables.

Revision ID: 054_create_social_proof
Revises: 053_strip_business_types_from_brand_settings
Create Date: 2026-04-20 00:02:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "054_create_social_proof"
down_revision = "053_strip_business_types_from_brand_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create 4 tables + indexes + seed from legacy JSONB."""
    # ─────────────────────────────────────────────────────────
    # 1. testimonials
    # ─────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS testimonials (
            id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID        NOT NULL,
            user_id             UUID        NOT NULL,
            author_name         VARCHAR(255) NOT NULL,
            author_role         VARCHAR(255),
            author_avatar_url   TEXT,
            content             TEXT,
            media_type          VARCHAR(20) NOT NULL DEFAULT 'text',
            media_url           TEXT,
            rating              SMALLINT,
            source_url          TEXT,
            captured_at         TIMESTAMPTZ,
            language            VARCHAR(8)  NOT NULL DEFAULT 'es',
            tags                TEXT[]      NOT NULL DEFAULT '{}',
            is_active           BOOLEAN     NOT NULL DEFAULT TRUE,
            deleted_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_testimonials_rating CHECK (rating IS NULL OR rating BETWEEN 1 AND 5)
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_testimonials_tenant_id ON testimonials(tenant_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_testimonials_tenant_active ON testimonials(tenant_id, is_active, deleted_at)",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_testimonials_tags ON testimonials USING GIN (tags)",
    )

    # ─────────────────────────────────────────────────────────
    # 2. authority_items
    # ─────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS authority_items (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            user_id         UUID        NOT NULL,
            entity_name     VARCHAR(255) NOT NULL,
            authority_type  VARCHAR(40) NOT NULL,
            context         TEXT,
            proof_url       TEXT,
            logo_url        TEXT,
            obtained_at     DATE,
            expires_at      DATE,
            is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
            deleted_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_authority_items_tenant_id ON authority_items(tenant_id)",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_authority_items_tenant_active "
        "ON authority_items(tenant_id, is_active, deleted_at)",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_authority_items_tenant_type ON authority_items(tenant_id, authority_type)",
    )

    # ─────────────────────────────────────────────────────────
    # 3. team_members
    # ─────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS team_members (
            id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id            UUID        NOT NULL,
            user_id              UUID        NOT NULL,
            name                 VARCHAR(255) NOT NULL,
            role                 VARCHAR(255),
            bio                  TEXT,
            headshot_url         TEXT,
            is_primary_voice     BOOLEAN     NOT NULL DEFAULT FALSE,
            gender               VARCHAR(20),
            communication_style  VARCHAR(40),
            personal_website     TEXT,
            personal_linkedin    TEXT,
            personal_instagram   TEXT,
            personal_tiktok      TEXT,
            personal_facebook    TEXT,
            work_whatsapp        VARCHAR(40),
            gallery              JSONB       NOT NULL DEFAULT '[]',
            sort_order           INTEGER     NOT NULL DEFAULT 0,
            deleted_at           TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_team_members_tenant_id ON team_members(tenant_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_team_members_tenant_sort ON team_members(tenant_id, sort_order)",
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_team_members_primary_voice_unique "
        "ON team_members(tenant_id) "
        "WHERE is_primary_voice = TRUE AND deleted_at IS NULL",
    )

    # ─────────────────────────────────────────────────────────
    # 4. social_proof_placements
    # ─────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS social_proof_placements (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            source_table    VARCHAR(30) NOT NULL,
            source_id       UUID        NOT NULL,
            surface_type    VARCHAR(30) NOT NULL,
            surface_ref_id  UUID,
            sort_order      INTEGER     NOT NULL DEFAULT 0,
            is_visible      BOOLEAN     NOT NULL DEFAULT TRUE,
            deleted_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_placements_tenant_id ON social_proof_placements(tenant_id)",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_placements_for_surface "
        "ON social_proof_placements(tenant_id, surface_type, surface_ref_id, "
        "is_visible, deleted_at)",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_placements_by_source "
        "ON social_proof_placements(source_table, source_id, deleted_at)",
    )
    # Partial unique: one live placement per (source, surface). COALESCE handles
    # NULL surface_ref_id (brand_homepage / sales_agent_kb are tenant-wide).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_placement_source_surface_alive
          ON social_proof_placements (
            source_table,
            source_id,
            surface_type,
            COALESCE(surface_ref_id, '00000000-0000-0000-0000-000000000000'::uuid)
          ) WHERE deleted_at IS NULL
        """,
    )

    # ─────────────────────────────────────────────────────────
    # 5. Seed from legacy JSONB — testimonials / authority_vault / team
    # ─────────────────────────────────────────────────────────
    # Each legacy row gets a deterministic UUID derived from (tenant_id, legacy_id
    # or array index) so re-runs land on the same row and the partial unique
    # index on placements prevents duplicates.
    op.execute(
        r"""
        DO $$
        DECLARE
            t_rec        RECORD;
            js_rec       JSONB;
            idx          INTEGER;
            new_id       UUID;
            legacy_id    TEXT;
            fallback_uid UUID;
        BEGIN
            FOR t_rec IN
                SELECT id AS tenant_id, config_json FROM tenants
                WHERE config_json ? 'brand_settings'
            LOOP
                -- Pick a user_id to attribute the seeded rows to: first active
                -- owner of the tenant, else a zero UUID (auditable as "seed").
                SELECT ut.user_id INTO fallback_uid
                FROM user_tenants ut
                WHERE ut.tenant_id = t_rec.tenant_id
                  AND ut.is_active = TRUE
                ORDER BY ut.created_at ASC NULLS LAST
                LIMIT 1;
                IF fallback_uid IS NULL THEN
                    fallback_uid := '00000000-0000-0000-0000-000000000000'::uuid;
                END IF;

                -- 5.1 testimonials
                idx := 0;
                FOR js_rec IN
                    SELECT jsonb_array_elements(
                        COALESCE(
                            t_rec.config_json #> '{brand_settings,testimonials}',
                            '[]'::jsonb
                        )
                    )
                LOOP
                    legacy_id := COALESCE(
                        js_rec->>'id',
                        'testimonial-' || idx::text
                    );
                    new_id := md5(t_rec.tenant_id::text || ':testimonial:' || legacy_id)::uuid;

                    INSERT INTO testimonials (
                        id, tenant_id, user_id, author_name, author_role,
                        author_avatar_url, content, media_type, rating, language
                    )
                    VALUES (
                        new_id,
                        t_rec.tenant_id,
                        fallback_uid,
                        COALESCE(
                            NULLIF(js_rec->>'author_name', ''),
                            NULLIF(js_rec->>'author', ''),
                            'Anónimo'
                        ),
                        COALESCE(
                            NULLIF(js_rec->>'author_role', ''),
                            NULLIF(js_rec->>'role', '')
                        ),
                        COALESCE(
                            NULLIF(js_rec->>'author_avatar', ''),
                            NULLIF(js_rec->>'avatar_url', '')
                        ),
                        COALESCE(
                            NULLIF(js_rec->>'content', ''),
                            NULLIF(js_rec->>'quote', '')
                        ),
                        COALESCE(NULLIF(js_rec->>'type', ''), 'text'),
                        CASE
                            WHEN (js_rec->>'rating') ~ '^[1-5]$'
                                THEN (js_rec->>'rating')::smallint
                            ELSE NULL
                        END,
                        'es'
                    )
                    ON CONFLICT (id) DO NOTHING;

                    INSERT INTO social_proof_placements (
                        tenant_id, source_table, source_id, surface_type,
                        surface_ref_id, sort_order
                    )
                    VALUES (
                        t_rec.tenant_id,
                        'testimonial',
                        new_id,
                        'brand_homepage',
                        NULL,
                        idx
                    )
                    ON CONFLICT DO NOTHING;

                    idx := idx + 1;
                END LOOP;

                -- 5.2 authority_items
                idx := 0;
                FOR js_rec IN
                    SELECT jsonb_array_elements(
                        COALESCE(
                            t_rec.config_json #> '{brand_settings,authority_vault}',
                            '[]'::jsonb
                        )
                    )
                LOOP
                    legacy_id := COALESCE(
                        js_rec->>'id',
                        'authority-' || idx::text
                    );
                    new_id := md5(t_rec.tenant_id::text || ':authority:' || legacy_id)::uuid;

                    INSERT INTO authority_items (
                        id, tenant_id, user_id, entity_name, authority_type,
                        context, proof_url, logo_url
                    )
                    VALUES (
                        new_id,
                        t_rec.tenant_id,
                        fallback_uid,
                        COALESCE(
                            NULLIF(js_rec->>'entity_name', ''),
                            NULLIF(js_rec->>'title', ''),
                            'Sin nombre'
                        ),
                        -- Map legacy Spanish free-text to canonical enum values.
                        -- Anything unknown drops to 'other'; users can reclassify
                        -- later via the UI.
                        CASE lower(COALESCE(js_rec->>'type', ''))
                            WHEN 'premio'         THEN 'award'
                            WHEN 'award'          THEN 'award'
                            WHEN 'prensa/media'   THEN 'media_mention'
                            WHEN 'prensa'         THEN 'media_mention'
                            WHEN 'media'          THEN 'media_mention'
                            WHEN 'media_mention'  THEN 'media_mention'
                            WHEN 'cliente'        THEN 'client_logo'
                            WHEN 'client'         THEN 'client_logo'
                            WHEN 'client_logo'    THEN 'client_logo'
                            WHEN 'certificacion'  THEN 'certification'
                            WHEN 'certificación' THEN 'certification'
                            WHEN 'certification'  THEN 'certification'
                            WHEN 'credencial'     THEN 'credential'
                            WHEN 'credential'     THEN 'credential'
                            WHEN 'publicacion'    THEN 'published_work'
                            WHEN 'publicación'   THEN 'published_work'
                            WHEN 'published_work' THEN 'published_work'
                            WHEN 'partnership'    THEN 'partnership'
                            WHEN 'alianza'        THEN 'partnership'
                            WHEN 'speaking'       THEN 'speaking'
                            WHEN 'ponencia'       THEN 'speaking'
                            WHEN 'charla'         THEN 'speaking'
                            WHEN 'podcast'        THEN 'podcast'
                            ELSE 'other'
                        END,
                        NULLIF(js_rec->>'context', ''),
                        COALESCE(
                            NULLIF(js_rec->>'proof_url', ''),
                            NULLIF(js_rec->>'url', '')
                        ),
                        NULLIF(js_rec->>'logo_url', '')
                    )
                    ON CONFLICT (id) DO NOTHING;

                    INSERT INTO social_proof_placements (
                        tenant_id, source_table, source_id, surface_type,
                        surface_ref_id, sort_order
                    )
                    VALUES (
                        t_rec.tenant_id,
                        'authority_item',
                        new_id,
                        'brand_homepage',
                        NULL,
                        idx
                    )
                    ON CONFLICT DO NOTHING;

                    idx := idx + 1;
                END LOOP;

                -- 5.3 team_members — legacy shape is
                --   team: { key_leadership: [...], culture_vibe, locations }
                -- OR team: [...] for older tenants.
                idx := 0;
                FOR js_rec IN
                    SELECT jsonb_array_elements(
                        COALESCE(
                            CASE
                                WHEN jsonb_typeof(t_rec.config_json #> '{brand_settings,team}')
                                     = 'array'
                                THEN t_rec.config_json #> '{brand_settings,team}'
                                ELSE t_rec.config_json #> '{brand_settings,team,key_leadership}'
                            END,
                            '[]'::jsonb
                        )
                    )
                LOOP
                    legacy_id := COALESCE(
                        js_rec->>'id',
                        'team-' || idx::text
                    );
                    new_id := md5(t_rec.tenant_id::text || ':team:' || legacy_id)::uuid;

                    INSERT INTO team_members (
                        id, tenant_id, user_id, name, role, bio, headshot_url,
                        is_primary_voice, gender, communication_style,
                        personal_website, personal_linkedin, personal_instagram,
                        personal_tiktok, personal_facebook, work_whatsapp,
                        gallery, sort_order
                    )
                    VALUES (
                        new_id,
                        t_rec.tenant_id,
                        fallback_uid,
                        COALESCE(NULLIF(js_rec->>'name', ''), 'Sin nombre'),
                        NULLIF(js_rec->>'role', ''),
                        NULLIF(js_rec->>'bio', ''),
                        NULLIF(js_rec->>'headshot_url', ''),
                        -- Only promote to primary_voice when legacy flag is TRUE
                        -- AND no other live team_member already holds the role
                        -- for this tenant. Legacy JSON sometimes has multiple
                        -- members flagged; we keep the first and demote the rest.
                        (
                            COALESCE((js_rec->>'is_primary_voice')::boolean, FALSE)
                            AND NOT EXISTS (
                                SELECT 1 FROM team_members existing
                                WHERE existing.tenant_id = t_rec.tenant_id
                                  AND existing.is_primary_voice = TRUE
                                  AND existing.deleted_at IS NULL
                            )
                        ),
                        NULLIF(js_rec->>'gender', ''),
                        NULLIF(js_rec->>'communication_style', ''),
                        NULLIF(js_rec->>'personal_website', ''),
                        NULLIF(js_rec->>'personal_linkedin', ''),
                        NULLIF(js_rec->>'personal_instagram', ''),
                        NULLIF(js_rec->>'personal_tiktok', ''),
                        NULLIF(js_rec->>'personal_facebook', ''),
                        NULLIF(js_rec->>'work_whatsapp', ''),
                        COALESCE(js_rec->'gallery', '[]'::jsonb),
                        idx
                    )
                    ON CONFLICT (id) DO NOTHING;

                    INSERT INTO social_proof_placements (
                        tenant_id, source_table, source_id, surface_type,
                        surface_ref_id, sort_order
                    )
                    VALUES (
                        t_rec.tenant_id,
                        'team_member',
                        new_id,
                        'brand_homepage',
                        NULL,
                        idx
                    )
                    ON CONFLICT DO NOTHING;

                    idx := idx + 1;
                END LOOP;
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """,
    )


def downgrade() -> None:
    """Drop the four social_proof tables. Legacy JSONB stays untouched."""
    op.execute("DROP TABLE IF EXISTS social_proof_placements")
    op.execute("DROP TABLE IF EXISTS team_members")
    op.execute("DROP TABLE IF EXISTS authority_items")
    op.execute("DROP TABLE IF EXISTS testimonials")
