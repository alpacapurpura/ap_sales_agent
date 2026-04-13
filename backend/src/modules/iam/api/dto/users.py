"""Users API endpoints."""

from pydantic import BaseModel


class TenantSchema(BaseModel):
    """Schema for tenant schema."""

    id: str
    name: str
    slug: str
    role: str
