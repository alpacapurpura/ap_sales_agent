"""strip business_types from tenants.config_json brand_settings

Migration 053 — removes the ``business_types`` key from the JSONB path
``tenants.config_json['brand_settings']['identity']``.

This is the cleanup step after migration 052, which backfilled the data into
the new ``tenant_profiles`` table. The JSONB key is now stale and must be
removed to prevent the BrandIdentity Pydantic model from accidentally reading
it (the field was removed from BrandIdentity in this sprint).

Idempotency:
  The UPDATE only touches rows where the key exists (the WHERE clause checks
  for the path). Safe to re-run.

Downgrade:
  No-op. We do NOT restore the JSONB key on downgrade because:
  1. Migration 052 downgrade already drops tenant_profiles.
  2. Restoring stale data into JSONB from a running system is unsafe.
  3. If you need to roll back past 052/053, use a DB snapshot.

Revision ID: 053_strip_business_types_from_brand_settings
Revises: 052_create_tenant_profiles
Create Date: 2026-04-20 00:01:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "053_strip_business_types_from_brand_settings"
down_revision = "052_create_tenant_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Remove business_types from brand_settings identity JSONB blob.

    Only touches rows where the key exists — idempotent on re-run.
    """
    op.execute(
        """
        UPDATE tenants
        SET config_json = jsonb_set(
            config_json,
            '{brand_settings,identity}',
            (config_json #> '{brand_settings,identity}')::jsonb - 'business_types'
        )
        WHERE config_json #> '{brand_settings,identity,business_types}' IS NOT NULL
        """
    )


def downgrade() -> None:
    """No-op — see module docstring for rationale.

    Restoring stale business_types data from a live system into the JSONB
    blob is unsafe. Roll back 052 + 053 together via DB snapshot only.
    """
