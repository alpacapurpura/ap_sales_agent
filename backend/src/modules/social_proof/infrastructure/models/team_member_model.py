"""SQLAlchemy model for the ``team_members`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TeamMemberModel(Base):
    """SQLAlchemy model mapping to the ``team_members`` table."""

    __tablename__ = "team_members"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)

    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    headshot_url = Column(Text, nullable=True)
    is_primary_voice = Column(Boolean, nullable=False, default=False)
    gender = Column(String(20), nullable=True)
    communication_style = Column(String(40), nullable=True)

    personal_website = Column(Text, nullable=True)
    personal_linkedin = Column(Text, nullable=True)
    personal_instagram = Column(Text, nullable=True)
    personal_tiktok = Column(Text, nullable=True)
    personal_facebook = Column(Text, nullable=True)
    work_whatsapp = Column(String(40), nullable=True)

    gallery = Column(JSONB, nullable=False, default=list)
    sort_order = Column(Integer, nullable=False, default=0)

    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index(
            "ix_team_members_tenant_sort",
            "tenant_id",
            "sort_order",
        ),
    )
