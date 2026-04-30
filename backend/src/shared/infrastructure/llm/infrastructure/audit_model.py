"""SQLAlchemy 2.0 model for the llm_config_audit table.

PI-2 S4 PR-1 db-registry-admin-ui.

Maps to ``llm_config_audit`` created by migration 117_llm_role_binding.

Append-only table — rows are NEVER updated or deleted. Preserves full
change history for compliance + MTTR audit trail.

Uses SA 2.0 ``Mapped`` / ``mapped_column`` — never legacy ``Column()``.
All datetimes are timezone-aware (``DateTime(timezone=True)``).
Default factory uses ``utc_now`` — never the deprecated utcnow call.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base
from src.shared.domain.datetime_utils import utc_now


class LLMConfigAuditModel(Base):
    """Immutable audit log for all admin actions on LLM role bindings.

    Actions: create | activate | deactivate | update_config | test_ping | rollback.

    ``before`` / ``after`` are JSONB snapshots of the binding state at the
    time of the action. ``before=NULL`` on create; ``after=NULL`` on
    rollback-to-detached.

    ``actor`` contains Clerk user_id (UUID-shaped string, non-PII per
    pii-sanitisation.md) or ``"system"`` for migration seeds.
    """

    __tablename__ = "llm_config_audit"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    __table_args__ = (
        # Hot-path for admin audit log display: last N entries by role
        Index(
            "ix_llm_config_audit_role_created",
            "role",
            "created_at",
        ),
        # Filtered index for tenant-scoped audit queries (S4 PR-2+)
        Index(
            "ix_llm_config_audit_tenant_created",
            "tenant_id",
            "created_at",
            postgresql_where="tenant_id IS NOT NULL",
        ),
    )
