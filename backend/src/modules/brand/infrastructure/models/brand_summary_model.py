"""Brand summary SQLAlchemy model.

Per-tenant living brand summary (≤800 chars Spanish neutro) regenerated
by the ARQ ``regen_brand_summary`` task on ``brand_section_updated``
events. Auto-injected into the copilot system prompt for the routes
target via ``brand/copilot_provider/context_inject.py``. Lives under
``brand`` (not ``copilot``) so brand owns its derived cache and the
copilot stays a pure consumer.

# [COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md
"""

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class BrandSummaryModel(Base):
    """SQLAlchemy model for ``brand_summary``."""

    __tablename__ = "brand_summary"
    __table_args__ = (CheckConstraint("chars_count <= 1000", name="ck_brand_summary_chars_le_1000"),)

    tenant_id = Column(UUID(as_uuid=True), primary_key=True)
    summary = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    model_used = Column(Text, nullable=False)
    chars_count = Column(Integer, nullable=False)
    last_section_changed = Column(Text, nullable=True)
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
        return f"<BrandSummary tenant={self.tenant_id} v={self.version} chars={self.chars_count}>"
