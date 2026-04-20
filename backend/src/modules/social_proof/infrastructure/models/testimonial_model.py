"""SQLAlchemy model for the ``testimonials`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TestimonialModel(Base):
    """SQLAlchemy model mapping to the ``testimonials`` table."""

    __tablename__ = "testimonials"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PG_UUID(as_uuid=True), nullable=False)

    author_name = Column(String(255), nullable=False)
    author_role = Column(String(255), nullable=True)
    author_avatar_url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    media_type = Column(String(20), nullable=False, default="text")
    media_url = Column(Text, nullable=True)
    rating = Column(SmallInteger, nullable=True)
    source_url = Column(Text, nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    language = Column(String(8), nullable=False, default="es")
    # PostgreSQL: TEXT[]. SQLite (tests): JSON fallback for dialect compat.
    tags = Column(
        ARRAY(Text).with_variant(JSON(), "sqlite"),
        nullable=False,
        default=list,
    )

    is_active = Column(Boolean, nullable=False, default=True)
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
        CheckConstraint("rating IS NULL OR rating BETWEEN 1 AND 5", name="ck_testimonials_rating"),
        Index(
            "ix_testimonials_tenant_active",
            "tenant_id",
            "is_active",
            "deleted_at",
        ),
    )
