"""Seed llm_role_binding from current .env values.

PI-2 S4 PR-1 db-registry-admin-ui.

Idempotent: conditional INSERT (WHERE NOT EXISTS active row for that role)
ensures re-runs are safe. Seed audit row also guarded by NOT EXISTS.

Source actor: 'system-migration-118'.

Seed values match docs/domains/llm-routing.md "Modelos activos hoy 2026-04-30"
and use ModelRole StrEnum values (lowercase) per core/enums.py ModelRole.

Revision ID: 118_llm_role_binding_seed_from_env
Revises: 117_llm_role_binding
Create Date: 2026-04-30
"""

from __future__ import annotations

from alembic import op

revision: str = "118_llm_role_binding_seed_from_env"
down_revision: str | None = "117_llm_role_binding"
branch_labels: str | None = None
depends_on: str | None = None

_SEED_DATA = [
    ("nano", "deepseek", "deepseek-v4-flash"),
    ("fast", "deepseek", "deepseek-v4-flash"),
    ("reasoning", "deepseek", "deepseek-reasoner"),
    ("agent", "kimi", "kimi-k2.6"),
    ("vision", "openai", "gpt-4o"),
    ("embedding", "openai", "text-embedding-3-large"),
]

_ACTOR = "system-migration-118"
_REASON = "Seed from .env at S4 PR-1 deploy"


def upgrade() -> None:
    """Insert one active binding per role, guarded by NOT EXISTS."""
    for role, provider, model in _SEED_DATA:
        # Insert active binding only if no active global row exists for this role.
        op.execute(f"""
            INSERT INTO llm_role_binding (role, provider, model, is_active, tenant_id, created_by, activated_at)
            SELECT
                '{role}',
                '{provider}',
                '{model}',
                TRUE,
                NULL,
                '{_ACTOR}',
                NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM llm_role_binding
                WHERE role = '{role}'
                  AND tenant_id IS NULL
                  AND is_active = TRUE
            )
        """)

        # Append audit row only if the binding above was just inserted
        # (created_by = our actor) and no prior audit row for this actor+role+action.
        op.execute(f"""
            INSERT INTO llm_config_audit (actor, action, role, tenant_id, after, reason)
            SELECT
                '{_ACTOR}',
                'create',
                '{role}',
                NULL,
                jsonb_build_object(
                    'provider', '{provider}',
                    'model', '{model}',
                    'is_active', TRUE
                ),
                '{_REASON}'
            WHERE EXISTS (
                SELECT 1 FROM llm_role_binding
                WHERE role = '{role}'
                  AND tenant_id IS NULL
                  AND is_active = TRUE
                  AND created_by = '{_ACTOR}'
            )
            AND NOT EXISTS (
                SELECT 1 FROM llm_config_audit
                WHERE actor = '{_ACTOR}'
                  AND role = '{role}'
                  AND action = 'create'
            )
        """)


def downgrade() -> None:
    """No-op — seed data is part of audit trail and must not be deleted.

    If manual cleanup is required:
      DELETE FROM llm_config_audit WHERE actor = 'system-migration-118';
      DELETE FROM llm_role_binding WHERE created_by = 'system-migration-118';
    """
