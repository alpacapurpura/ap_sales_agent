"""Domain Entity domain definitions."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from luana_core_platform.domain.base_entity import BaseEntity


class DomainStatus(StrEnum):
    """Enumerate domain status values."""

    PENDING_VERIFICATION = "pending_verification"
    VERIFYING = "verifying"
    ACTIVE = "active"
    FAILED = "failed"
    SUSPENDED = "suspended"


class DomainType(StrEnum):
    """Enumerate domain type values."""

    PLATFORM = "platform"
    CUSTOM = "custom"


class TenantDomain(BaseEntity):
    """Represent tenant domain."""

    id: UUID
    tenant_id: UUID
    hostname: str
    domain_type: DomainType
    status: DomainStatus = DomainStatus.PENDING_VERIFICATION
    is_primary: bool = False
    cloudflare_hostname_id: str | None = None
    ssl_status: str | None = None
    verification_method: str | None = None
    verification_cname_target: str | None = None
    verification_txt_name: str | None = None
    verification_txt_value: str | None = None
    verified_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
