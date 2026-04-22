"""SQLAlchemy model for asset ↔ domain entity links.

An ``AssetLinkModel`` connects an asset to any domain entity (offer, brand,
flow_phase, buyer_persona, …) with a typed role. This is the polymorphic
attachment that lets the sales_agent auto-forward the right files in the
right phase without hardcoding ids anywhere.

See ``.claude/rules/`` and the asset-lifecycle design doc.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AssetLinkModel(Base):
    """Polymorphic link: asset → (entity_type, entity_id) with a role."""

    __tablename__ = "asset_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    asset_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )
    # entity_type is a free string at the DB level — validation is enforced
    # in the domain layer via an enum, keeping the DB schema open for new
    # linkable modules without migrations.
    entity_type = Column(String(40), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    role = Column(String(40), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<AssetLink asset={self.asset_id} {self.entity_type}={self.entity_id} role={self.role}>"
