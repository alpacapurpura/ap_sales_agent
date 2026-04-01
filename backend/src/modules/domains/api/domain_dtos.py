from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.domains.domain.domain_entity import DomainStatus, DomainType


class DomainCreate(BaseModel):
    hostname: str = Field(
        min_length=4,
        max_length=253,
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(\.[a-zA-Z]{2,})$",
        description="Valid fully-qualified domain name (e.g. go.example.com)",
    )
    domain_type: DomainType


class DomainSetPrimary(BaseModel):
    is_primary: bool


class DomainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    hostname: str
    domain_type: DomainType
    status: DomainStatus
    is_primary: bool
    ssl_status: Optional[str] = None
    verification_method: Optional[str] = None
    verification_cname_target: Optional[str] = None
    verification_txt_name: Optional[str] = None
    verification_txt_value: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
