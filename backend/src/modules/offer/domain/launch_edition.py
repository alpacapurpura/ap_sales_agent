"""LaunchEdition domain entity — represents one launch of an offer."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import model_validator

from src.modules.offer.domain.offer import PricingStructure
from src.shared.domain.base_entity import BaseEntity


class EditionStatus(StrEnum):
    """Edition Status enumeration."""

    DRAFT = "draft"
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LaunchEdition(BaseEntity):
    """One launch/edition of an offer (cohort, event date, workshop run)."""

    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    edition_name: str
    edition_number: int

    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

    pricing_override: list[PricingStructure] | None = None

    capacity: int | None = None
    enrollment_count: int = 0

    status: EditionStatus = EditionStatus.DRAFT

    location_override: dict[str, Any] | None = None
    notes: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> LaunchEdition:
        """Validate dates."""
        if self.end_date and self.end_date < self.start_date:
            msg = "end_date cannot be before start_date"
            raise ValueError(msg)
        if self.registration_start and self.registration_end and self.registration_end < self.registration_start:
            msg = "registration_end cannot be before registration_start"
            raise ValueError(msg)
        return self


class LaunchEditionCreate(BaseEntity):
    """DTO for creating a new edition."""

    edition_name: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionUpdate(BaseEntity):
    """DTO for patching an edition (all fields optional)."""

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str | None = None
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    enrollment_count: int | None = None
    status: EditionStatus | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None
