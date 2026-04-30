"""SQLAlchemy 2.0 model for the llm_role_binding table.

PI-2 S4 PR-1 db-registry-admin-ui.

Maps to ``llm_role_binding`` created by migration 117_llm_role_binding.

Uses SA 2.0 ``Mapped`` / ``mapped_column`` — never legacy ``Column()``.
All datetimes are timezone-aware (``DateTime(timezone=True)``).
Default factory uses ``utc_now`` — never the deprecated utcnow call.

Tenant isolation note: ``tenant_id IS NULL`` means global default.
This is the documented exception pattern (same as ``model_pricing_snapshot``
and ``plan_config``) for global admin catalogs. PR-1 ships only global rows.
Per-tenant rows deferred to S4 PR-2.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base
from src.shared.domain.datetime_utils import utc_now


class LLMRoleBindingModel(Base):
    """Persistent LLM role binding — SSoT runtime model selection per role.

    One row = one candidate model binding for a given role.
    At most one active row per (role, tenant_id) enforced via partial UNIQUE
    index ``uq_llm_role_binding_active_per_role`` (migration 117).

    Lifecycle:
    - Created INACTIVE via admin Streamlit or migration seed.
    - Promoted ACTIVE via LLMConfigService.activate (atomic transaction
      that also deactivates any prior active row for the same role).
    - Deactivated via LLMConfigService.deactivate (soft — row preserved
      for audit trail; ``deactivated_at`` timestamp set).
    """

    __tablename__ = "llm_role_binding"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    eval_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # B-tree composite index for hot-path resolve queries
        # WHERE role=X AND tenant_id IS NULL AND is_active=TRUE
        Index(
            "ix_llm_role_binding_role_tenant_active",
            "role",
            "tenant_id",
            "is_active",
        ),
    )
