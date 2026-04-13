"""Domain Dtos API endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.tenant_domains.domain.domain_entity import DomainStatus, DomainType


class DomainCreate(BaseModel):
    """Schema for domain create."""

    hostname: str = Field(
        min_length=4,
        max_length=253,
        pattern=r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(\.[a-zA-Z]{2,})$",
        description="Valid fully-qualified domain name (e.g. go.example.com)",
    )
    domain_type: DomainType


class DomainSetPrimary(BaseModel):
    """Schema for domain set primary."""

    is_primary: bool


class DomainResponse(BaseModel):
    """Schema for domain response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    hostname: str
    domain_type: DomainType
    status: DomainStatus
    is_primary: bool
    ssl_status: str | None = None
    verification_method: str | None = None
    verification_cname_target: str | None = None
    verification_txt_name: str | None = None
    verification_txt_value: str | None = None
    verified_at: datetime | None = None
    created_at: datetime | None = None


class DomainConflictDetail(BaseModel):
    """Schema for domain conflict detail."""

    code: str = "DOMAIN_CONFLICT"
    provider: str
    suggestion: str
    message: str


class DnsRecord(BaseModel):
    """Schema for dns record."""

    type: str
    name: str
    target: str | None = None
    value: str | None = None


class DomainInstructionsResponse(BaseModel):
    """Schema for domain instructions response."""

    hostname: str
    domain_type: DomainType
    status: DomainStatus
    cname_record: DnsRecord | None = None
    txt_record: DnsRecord | None = None
