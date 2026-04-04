from enum import Enum
from typing import Optional
from uuid import UUID
from datetime import datetime

from src.shared.domain.base_entity import BaseEntity


class DomainStatus(str, Enum):
    PENDING_VERIFICATION = "pending_verification"
    VERIFYING = "verifying"
    ACTIVE = "active"
    FAILED = "failed"
    SUSPENDED = "suspended"


class DomainType(str, Enum):
    PLATFORM = "platform"
    CUSTOM = "custom"


class TenantDomain(BaseEntity):
    id: UUID
    tenant_id: UUID
    hostname: str
    domain_type: DomainType
    status: DomainStatus = DomainStatus.PENDING_VERIFICATION
    is_primary: bool = False
    cloudflare_hostname_id: Optional[str] = None
    ssl_status: Optional[str] = None
    verification_method: Optional[str] = None
    verification_cname_target: Optional[str] = None
    verification_txt_name: Optional[str] = None
    verification_txt_value: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
