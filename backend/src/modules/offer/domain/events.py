"""Domain events for the offer module.

Emitted by application services. Subscribers live in the event bus and
other modules. For the offer header feature the bus is a no-op; events
still flow through the same shape so downstream work can subscribe later
without refactoring the producers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity

if TYPE_CHECKING:
    from datetime import datetime

    from src.modules.offer.domain.enums import (
        AssetType,
        KnowledgeSourceStatus,
    )
    from src.modules.offer.domain.lifecycle import OfferLifecycleStatus


class DomainEvent(BaseEntity):
    event_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    occurred_at: datetime


class OfferStatusChanged(DomainEvent):
    offer_id: UUID
    from_status: OfferLifecycleStatus
    to_status: OfferLifecycleStatus
    actor_user_id: UUID | None = None


class OfferAssetCreated(DomainEvent):
    offer_id: UUID
    asset_id: UUID
    type: AssetType
    source: str


class OfferAssetDeleted(DomainEvent):
    offer_id: UUID
    asset_id: UUID


class KnowledgeSourceCreated(DomainEvent):
    offer_id: UUID
    source_id: UUID
    type: str


class KnowledgeSourceIndexed(DomainEvent):
    offer_id: UUID
    source_id: UUID
    chunk_count: int
    status: KnowledgeSourceStatus


class KnowledgeSourceDeleted(DomainEvent):
    offer_id: UUID
    source_id: UUID


class LandingGenerationRequested(DomainEvent):
    offer_id: UUID
    snapshot_version: str
    job_id: UUID


class LandingRegenerationRequested(DomainEvent):
    offer_id: UUID
    previous_snapshot_version: str | None
    snapshot_version: str
    job_id: UUID


class LandingPublished(DomainEvent):
    offer_id: UUID
    landing_page_id: UUID


class LandingUnpublished(DomainEvent):
    offer_id: UUID
    landing_page_id: UUID
    reason: str


__all__ = [
    "DomainEvent",
    "KnowledgeSourceCreated",
    "KnowledgeSourceDeleted",
    "KnowledgeSourceIndexed",
    "LandingGenerationRequested",
    "LandingPublished",
    "LandingRegenerationRequested",
    "LandingUnpublished",
    "OfferAssetCreated",
    "OfferAssetDeleted",
    "OfferStatusChanged",
]
