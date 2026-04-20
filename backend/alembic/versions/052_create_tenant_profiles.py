"""create tenant_profiles table and backfill from brand_settings JSONB

Migration 052 — tenant_profile bounded context (Sprint 2026-04-20).

Creates ``tenant_profiles`` as the SSoT for ``business_types``:
- PK on ``tenant_id`` (1:1 with tenants, FK with CASCADE delete).
- GIN index for array containment queries.
- btree index on ``declared_at`` for onboarding-completion queries.

Backfill step:
  Copies ``business_types`` from
  ``tenants.config_json['brand_settings']['identity']['business_types']``
  into the new table. Tenants with malformed or missing data get a row with
  ``business_types = '{}'`` and ``declared_at = NULL`` — the gating middleware
  will catch these and route them through the onboarding flow.

Idempotency:
  All DDL uses ``IF NOT EXISTS``. The backfill ``INSERT ... ON CONFLICT DO NOTHING``
  guarantees re-runs are safe.

Downgrade:
  Drops the table. Data is lost on downgrade — no attempt to restore the JSONB
  key (migration 053 strips it from brand_settings). If you need to roll back
  past this migration in production, restore from a DB snapshot.

Revision ID: 052_create_tenant_profiles
Revises: 051_launch_editions_variant_structure_default
Create Date: 2026-04-20 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "052_create_tenant_profiles"
down_revision = "051_launch_editions_variant_structure_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create tenant_profiles table with indexes and backfill from JSONB."""
    # ── 1. Create table ────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_profiles (
            tenant_id   UUID        PRIMARY KEY
                            REFERENCES tenants(id) ON DELETE CASCADE,
            business_types TEXT[]  NOT NULL DEFAULT '{}',
            declared_at TIMESTAMPTZ,
            last_business_types_change_at TIMESTAMPTZ,
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    # ── 2. Indexes ─────────────────────────────────────────────────────────
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_profiles_business_types
            ON tenant_profiles USING GIN (business_types)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_profiles_declared_at
            ON tenant_profiles (declared_at)
        """
    )

    # ── 3. Backfill from brand_settings JSONB ─────────────────────────────
    # Uses a PL/pgSQL DO block so we can iterate rows, handle malformed data,
    # and emit RAISE NOTICE for skipped tenants without aborting the migration.
    #
    # Logic:
    # - If the JSONB path 'brand_settings → identity → business_types' exists
    #   and is a valid JSON array of strings, use it. Map known legacy aliases.
    # - Otherwise, insert with empty array and NULL declared_at.
    # - ON CONFLICT DO NOTHING ensures idempotency on re-run.
    op.execute(
        r"""
        DO $$
        DECLARE
            rec          RECORD;
            raw_arr      JSONB;
            bt_array     TEXT[];
            elem         TEXT;
            alias_map    JSONB;
        BEGIN
            -- Legacy slug → canonical alias map (mirrors identity.py)
            alias_map := '{
                "consultor_asesor":        "consultor_profesional",
                "educador_infoproductor":  "academia_infoproductor",
                "creador_contenido":       "academia_infoproductor"
            }'::JSONB;

            FOR rec IN SELECT id, config_json FROM tenants LOOP
                raw_arr := rec.config_json #> '{brand_settings,identity,business_types}';

                IF raw_arr IS NULL OR jsonb_typeof(raw_arr) <> 'array' THEN
                    -- No data or malformed — insert empty row for gating middleware.
                    INSERT INTO tenant_profiles
                        (tenant_id, business_types, declared_at,
                         last_business_types_change_at, updated_at)
                    VALUES (rec.id, '{}', NULL, NULL, NOW())
                    ON CONFLICT (tenant_id) DO NOTHING;

                    IF raw_arr IS NOT NULL THEN
                        RAISE NOTICE 'tenant_profiles backfill: skipped malformed '
                            'business_types for tenant % (value: %)',
                            rec.id, raw_arr;
                    END IF;
                    CONTINUE;
                END IF;

                -- Build TEXT[] applying legacy alias map.
                bt_array := ARRAY[]::TEXT[];
                FOR elem IN SELECT jsonb_array_elements_text(raw_arr) LOOP
                    IF alias_map ? elem THEN
                        elem := alias_map ->> elem;
                    END IF;
                    -- Only append if not already present (deduplicate).
                    IF NOT (elem = ANY(bt_array)) THEN
                        bt_array := bt_array || elem;
                    END IF;
                END LOOP;

                INSERT INTO tenant_profiles
                    (tenant_id, business_types, declared_at,
                     last_business_types_change_at, updated_at)
                VALUES (
                    rec.id,
                    bt_array,
                    NOW(),   -- declared_at: prior tenants treated as declared now
                    NOW(),   -- last_business_types_change_at
                    NOW()
                )
                ON CONFLICT (tenant_id) DO NOTHING;

            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """
    )


def downgrade() -> None:
    """Drop tenant_profiles.

    Data is lost. Downgrade past this migration in production requires a DB
    snapshot restore, not an Alembic downgrade. The JSONB key was removed by
    migration 053 and is not restored here.
    """
    op.execute("DROP TABLE IF EXISTS tenant_profiles")
