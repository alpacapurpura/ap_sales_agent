"""Copilot inspiration SQLAlchemy model — F4 URL contextual scratchpad.

Per-conversation cache of URLs the user has pasted as inspiration.
Lives in DB (not deepagents StateBackend) so the inspirations table in
the system prompt can be rebuilt from scratch on every turn even after
conversation rehydration. The ephemeral ``/inspirations/{slug}.md``
file the deep-agent subagent writes during a single turn is a separate
concern handled inside the subagent — DB row is the authoritative
cross-turn surface.

# [COPILOT-INSPIRATION-F4] -> docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
"""

import uuid

from sqlalchemy import Column, DateTime, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base
from src.shared.domain.datetime_utils import utc_now


class CopilotInspirationModel(Base):
    """SQLAlchemy model for ``copilot_inspiration``."""

    __tablename__ = "copilot_inspiration"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "slug",
            name="uq_copilot_inspiration_conversation_slug",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), nullable=False)
    slug = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    why = Column(Text, nullable=False, default="")
    domain = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    summary = Column(Text, nullable=False)
    sub_elements = Column(JSONB, nullable=False, default=dict)
    brand_relevance_score = Column(Numeric(3, 2), nullable=False, default=0.5)
    content_md = Column(Text, nullable=False)
    og_image = Column(Text, nullable=True)
    # Python-side default gives microsecond precision in SQLite tests too;
    # server_default kept as a fallback for direct SQL inserts (migrations
    # backfill, admin tools).
    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CopilotInspiration conv={self.conversation_id} slug={self.slug}>"
