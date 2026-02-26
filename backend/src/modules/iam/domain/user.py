from typing import List, Optional, Dict, Any
from pydantic import ConfigDict, EmailStr
from datetime import datetime
from uuid import UUID
from src.shared.domain.base_entity import BaseEntity

class User(BaseEntity):
    """
    System User / Admin / Dashboard User Domain Model.
    """
    id: UUID
    full_name: Optional[str] = None
    email: EmailStr
    phone: Optional[str] = None
    clerk_id: Optional[str] = None
    role: str = "admin"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Context (Injected at runtime, not stored in DB User table directly)
    tenant_id: Optional[UUID] = None

class SystemUserProfile(BaseEntity):
    """
    Response model for current authenticated user profile.
    """
    id: str
    full_name: Optional[str]
    email: str
    tenant: Optional[Dict[str, Any]] = None # Simplified tenant info

class TeamMemberCreate(BaseEntity):
    """
    Request model for adding a new user to the team.
    """
    full_name: str
    email: str
    password: str
