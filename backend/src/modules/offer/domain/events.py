"""Domain events for the offer module.

Emitted by application services. Subscribers live in the event bus and
other modules. For the offer header feature the bus is a no-op; events
still flow through the same shape so downstream work can subscribe later
without refactoring the producers.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import Field

from src.modules.offer.domain.enums import (
    AssetType,
    KnowledgeSourceStatus,
    OfferArchetype,
)
from src.modules.offer.domain.lifecycle import OfferLifecycleStatus
from src.shared.domain.base_entity import BaseEntity


class DomainEvent(BaseEntity):
    """Domain Event."""

    event_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    occurred_at: datetime


class OfferStatusChanged(DomainEvent):
    """Offer Status Changed."""

    offer_id: UUID
    from_status: OfferLifecycleStatus
    to_status: OfferLifecycleStatus
    actor_user_id: UUID | None = None


class OfferAssetCreated(DomainEvent):
    """Offer Asset Created."""

    offer_id: UUID
    asset_id: UUID
    type: AssetType
    source: str


class OfferAssetDeleted(DomainEvent):
    """Offer Asset Deleted."""

    offer_id: UUID
    asset_id: UUID


class KnowledgeSourceCreated(DomainEvent):
    """Knowledge Source Created."""

    offer_id: UUID
    source_id: UUID
    type: str


class KnowledgeSourceIndexed(DomainEvent):
    """Knowledge Source Indexed."""

    offer_id: UUID
    source_id: UUID
    chunk_count: int
    status: KnowledgeSourceStatus


class KnowledgeSourceDeleted(DomainEvent):
    """Knowledge Source Deleted."""

    offer_id: UUID
    source_id: UUID


class LandingGenerationRequested(DomainEvent):
    """Landing Generation Requested."""

    offer_id: UUID
    snapshot_version: str
    job_id: UUID


class LandingRegenerationRequested(DomainEvent):
    """Landing Regeneration Requested."""

    offer_id: UUID
    previous_snapshot_version: str | None
    snapshot_version: str
    job_id: UUID


class LandingPublished(DomainEvent):
    """Landing Published."""

    offer_id: UUID
    landing_page_id: UUID


class LandingUnpublished(DomainEvent):
    """Landing Unpublished."""

    offer_id: UUID
    landing_page_id: UUID
    reason: str


class OfferCreated(DomainEvent):
    """Fires when an offer is first persisted.

    Consumers can preload analytics, trigger onboarding copilot flows, or
    hook into placeholder creation (currently handled atomically inline by
    ``OfferService``).
    """

    offer_id: UUID
    archetype: OfferArchetype
    supports_editions: bool


class EditionCreated(DomainEvent):
    """Fires when a launch edition is persisted (placeholder or otherwise).

    Subscribers can preload analytics dimensions, start cache warmup, or
    notify copilot about a new edition to track.
    """

    offer_id: UUID
    edition_id: UUID
    edition_number: int
    is_placeholder: bool
    cloned_from_edition_id: UUID | None = None


__all__ = [
    "DomainEvent",
    "EditionCreated",
    "KnowledgeSourceCreated",
    "KnowledgeSourceDeleted",
    "KnowledgeSourceIndexed",
    "LandingGenerationRequested",
    "LandingPublished",
    "LandingRegenerationRequested",
    "LandingUnpublished",
    "OfferAssetCreated",
    "OfferAssetDeleted",
    "OfferCreated",
    "OfferStatusChanged",
]
