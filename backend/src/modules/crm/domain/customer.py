from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.shared.domain.base_entity import BaseEntity


class CustomerIdentity(BaseEntity):
    id: UUID
    profile_id: UUID
    tenant_id: UUID | None = None

    type: IdentityType
    value: str

    is_primary: bool = False
    verification_status: str = "unverified"

    last_seen_at: datetime | None = None


class CustomerProfile(BaseEntity):
    id: UUID
    tenant_id: UUID | None = None

    # Unified Identity
    primary_email: str | None = None
    primary_phone: str | None = None
    full_name: str | None = None

    # Scoring & Segmentation
    lifecycle_stage: LifecycleStage | None = LifecycleStage.SUBSCRIBER
    lead_score: float = 0.0
    rfm_segment: str | None = None  # e.g. "Champions", "At Risk"

    # Lifecycle & Activity
    lifetime_value: float = 0.0
    last_activity_at: datetime | None = None
    is_inactive: bool = False
    first_conversion_at: datetime | None = None
    first_seen_at: datetime | None = None
    lead_source: str | None = None
    lead_source_detail: str | None = None

    # Metadata
    traits: dict[str, Any] = Field(default_factory=dict)  # Demographics, etc.
    computed_traits: dict[str, Any] = Field(
        default_factory=dict,
    )  # LTV, Last Seen, etc.

    created_at: datetime | None = None
    updated_at: datetime | None = None

    identities: list[CustomerIdentity] = []
