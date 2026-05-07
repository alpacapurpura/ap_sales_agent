"""SQLAlchemy model for ``eval_synthetic_tenants``.

Lookup table for synthetic tenant isolation (D4 arch decision — 03-arch-be.md §1).

Rationale:
- Instead of adding ``is_eval_synthetic BOOLEAN`` column to 5+ business tables
  (tenants, brand, personality_profile, products, buyer_personas), a single
  lookup table allows Streamlit prod queries to filter via:
      WHERE tenant_id NOT IN (
          SELECT tenant_id FROM eval_synthetic_tenants WHERE deleted_at IS NULL
      )
- tenant_id = uuid5(NAMESPACE_DNS, f"eval-{slug}") deterministic (D2).
- Soft-delete (deleted_at) used for teardown idempotency — not hard delete.

Origin: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
R5 schema-mirror exception (.claude/rules/backend-ddd.md).
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from src.shared.domain.base_entity import Base


class EvalSyntheticTenantModel(Base):
    """ORM mapping for ``eval_synthetic_tenants``.

    Each row marks a tenant UUID as synthetic / eval-only.
    The archetype_slug corresponds to Story A TenantContext seeds.
    """

    __tablename__ = "eval_synthetic_tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    archetype_slug = Column(String(64), nullable=False)
    seeded_at = Column(DateTime(timezone=True), nullable=False)
    # Soft-delete for idempotent teardown (fixture teardown marks deleted_at).
    # Hard delete FORBIDDEN (.claude/rules/backend-ddd.md soft-delete only).
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        """Return a debug-friendly summary."""
        return f"<EvalSyntheticTenant tenant_id={self.tenant_id} archetype_slug={self.archetype_slug}>"
