"""Copilot pinned memory SQLAlchemy model.

StoreBackend (per-user opt-in, persistent cross-thread). Distinct from
the ephemeral StateBackend that lives inside ``CopilotState`` for a
single conversation. F2 ships the table + repo; the ``pin_to_memory``
tool that promotes ephemeral → persistent is wired in F4.
"""

import uuid

from sqlalchemy import Column, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotPinnedMemoryModel(Base):
    """SQLAlchemy model for ``copilot_pinned_memory``."""

    __tablename__ = "copilot_pinned_memory"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            "path",
            name="uq_copilot_pinned_memory_tenant_user_path",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    path = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    pinned_from_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CopilotPinnedMemory tenant={self.tenant_id} user={self.user_id} path={self.path}>"
