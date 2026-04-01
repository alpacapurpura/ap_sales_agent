from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.domains.domain.domain_entity import DomainStatus, DomainType


class DomainCreate(BaseModel):
    hostname: str
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
