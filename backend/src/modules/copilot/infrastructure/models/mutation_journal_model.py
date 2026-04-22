"""MutationJournalModel — SQLAlchemy model for copilot_mutation_journal table."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class MutationJournalModel(Base):
    """Audit trail for copilot-applied field mutations.

    Each row records a single field change made by the copilot agent, with
    enough information to revert it.
    """

    __tablename__ = "copilot_mutation_journal"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    domain = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    field_path = Column(String, nullable=False)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    applied_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reverted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<MutationJournal id={self.id} domain={self.domain} field={self.field_path}>"
