"""User domain definitions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import EmailStr

from src.shared.domain.base_entity import BaseEntity


class User(BaseEntity):
    """System User / Admin / Dashboard User Domain Model."""

    id: UUID
    full_name: str | None = None
    email: EmailStr
    phone: str | None = None
    clerk_id: str | None = None
    role: str = "admin"
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Context (Injected at runtime, not stored in DB User table directly)
    tenant_id: UUID | None = None


class SystemUserProfile(BaseEntity):
    """Response model for current authenticated user profile."""

    id: str
    full_name: str | None
    email: str
    tenant: Any | None = None  # Simplified tenant info (TenantProfile)


class TeamMemberCreate(BaseEntity):
    """Request model for adding a new user to the team."""

    full_name: str
    email: str
    password: str


class TeamMemberSchema(BaseEntity):
    """Response model for team members listing."""

    id: str
    full_name: str | None
    email: str
    role: str
    is_active: bool
    created_at: datetime | None
