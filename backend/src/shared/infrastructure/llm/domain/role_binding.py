"""LLMRoleBinding and LLMConfigAuditEntry domain value objects.

PI-2 S4 PR-1 db-registry-admin-ui.

These are pure Python dataclasses (no SQLAlchemy imports) representing
the immutable domain model for LLM model registry runtime hot-swap.

Invariants:
- LLMRoleBinding: at most 1 active row per (role, tenant_id IS NULL) global.
  Partial UNIQUE index in migration 117 enforces this at DB level.
- LLMConfigAuditEntry: append-only, never mutated post-insert.
- Both are frozen (immutable) by design — domain events, not entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from src.core.enums import AIProvider, ModelRole

AuditAction = Literal["create", "activate", "deactivate", "update_config", "test_ping", "rollback"]


@dataclass(frozen=True, slots=True)
class LLMRoleBinding:
    """Immutable value object. Single active row per (role, tenant_id NULL global).

    Persisted shape: row in ``llm_role_binding`` table.

    Invariants (DB partial unique index enforces):
    - At most 1 row WHERE role=X AND tenant_id IS NULL AND is_active=TRUE.
    - At most 1 row WHERE role=X AND tenant_id=Y AND is_active=TRUE
      (per-tenant; deferred S4 PR-2).
    - ``model`` MUST exist in ``model_pricing_snapshot WHERE valid_to IS NULL``
      (validated at app-layer via LLMConfigService.activate, NOT via DB FK —
      see migration 117 notes). PR-1 enforces global-only (tenant_id IS NULL).
    """

    id: UUID
    role: ModelRole
    provider: AIProvider
    model: str  # wire-name as known to LiteLLM Proxy (e.g. "deepseek-v4-flash")
    is_active: bool
    config: dict[str, Any]  # JSONB: temperature, max_tokens, top_p, etc.
    created_at: datetime
    eval_score: Decimal | None = None  # populated when S5 eval-gate ships
    notes: str | None = None
    created_by: str | None = None
    activated_at: datetime | None = None
    deactivated_at: datetime | None = None
    tenant_id: UUID | None = None  # NULL = global default; per-tenant deferred S4 PR-2


@dataclass(frozen=True, slots=True)
class LLMConfigAuditEntry:
    """Append-only audit entry. Persisted as row in ``llm_config_audit``.

    Never mutated after creation. Records every admin action on role bindings
    for compliance and MTTR audit trail (rollback MTTR target <30s).
    """

    id: UUID
    actor: str  # admin user (Clerk user_id or "system" for migrations)
    action: AuditAction
    role: str  # ModelRole.value
    created_at: datetime
    tenant_id: UUID | None = None
    before: dict[str, Any] | None = None  # previous state JSONB (None on create)
    after: dict[str, Any] | None = None  # new state JSONB (None on rollback to detached)
    reason: str | None = None
