import uuid

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class UserModel(Base):
    """
    System User / Admin / Dashboard User.
    Separated from 'Lead' (Chatbot User).
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=True)
    email = Column(
        String, nullable=False, unique=True
    )  # Email is mandatory for system users
    phone = Column(String, nullable=True)

    # Auth / Role
    clerk_id = Column(String, unique=True, nullable=True)  # Linked Clerk User ID
    role = Column(String, default="admin")  # admin, member, viewer
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Tenant Link
    # Note: 'UserTenantModel' is defined as a string to avoid circular imports if in same module but different file
    tenants = relationship(
        "TenantModel", secondary="user_tenants", back_populates="users"
    )
