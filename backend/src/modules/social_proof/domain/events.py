"""Domain events emitted by the social_proof bounded context.

Events are published via :class:`src.shared.domain.events.EventBus` after
commit. Subscribers live in other modules (sales_agent KB, landing cache,
copilot embeddings) and react asynchronously without import-time coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.shared.domain.events import DomainEvent

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.social_proof.domain.enums import SourceTable, SurfaceType


# ─────────────────────────────────────────────
# Testimonial events
# ─────────────────────────────────────────────


@dataclass
class TestimonialCreated(DomainEvent):
    """Emitted after a new Testimonial row is committed."""

    @classmethod
    def create(cls, tenant_id: UUID, testimonial_id: UUID) -> TestimonialCreated:
        """Build a ``testimonial_created`` event."""
        return cls(
            event_name="testimonial_created",
            tenant_id=tenant_id,
            payload={"testimonial_id": str(testimonial_id)},
        )


@dataclass
class TestimonialUpdated(DomainEvent):
    """Emitted after a Testimonial row is patched."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        testimonial_id: UUID,
        changed_fields: list[str],
    ) -> TestimonialUpdated:
        """Build a ``testimonial_updated`` event."""
        return cls(
            event_name="testimonial_updated",
            tenant_id=tenant_id,
            payload={
                "testimonial_id": str(testimonial_id),
                "changed_fields": list(changed_fields),
            },
        )


@dataclass
class TestimonialSoftDeleted(DomainEvent):
    """Emitted after a Testimonial row is soft-deleted."""

    @classmethod
    def create(cls, tenant_id: UUID, testimonial_id: UUID) -> TestimonialSoftDeleted:
        """Build a ``testimonial_soft_deleted`` event."""
        return cls(
            event_name="testimonial_soft_deleted",
            tenant_id=tenant_id,
            payload={"testimonial_id": str(testimonial_id)},
        )


# ─────────────────────────────────────────────
# AuthorityItem events
# ─────────────────────────────────────────────


@dataclass
class AuthorityItemCreated(DomainEvent):
    """Emitted after a new AuthorityItem row is committed."""

    @classmethod
    def create(cls, tenant_id: UUID, authority_item_id: UUID) -> AuthorityItemCreated:
        """Build an ``authority_item_created`` event."""
        return cls(
            event_name="authority_item_created",
            tenant_id=tenant_id,
            payload={"authority_item_id": str(authority_item_id)},
        )


@dataclass
class AuthorityItemUpdated(DomainEvent):
    """Emitted after an AuthorityItem row is patched."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        authority_item_id: UUID,
        changed_fields: list[str],
    ) -> AuthorityItemUpdated:
        """Build an ``authority_item_updated`` event."""
        return cls(
            event_name="authority_item_updated",
            tenant_id=tenant_id,
            payload={
                "authority_item_id": str(authority_item_id),
                "changed_fields": list(changed_fields),
            },
        )


@dataclass
class AuthorityItemSoftDeleted(DomainEvent):
    """Emitted after an AuthorityItem row is soft-deleted."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        authority_item_id: UUID,
    ) -> AuthorityItemSoftDeleted:
        """Build an ``authority_item_soft_deleted`` event."""
        return cls(
            event_name="authority_item_soft_deleted",
            tenant_id=tenant_id,
            payload={"authority_item_id": str(authority_item_id)},
        )


# ─────────────────────────────────────────────
# TeamMember events
# ─────────────────────────────────────────────


@dataclass
class TeamMemberCreated(DomainEvent):
    """Emitted after a new TeamMember row is committed."""

    @classmethod
    def create(cls, tenant_id: UUID, team_member_id: UUID) -> TeamMemberCreated:
        """Build a ``team_member_created`` event."""
        return cls(
            event_name="team_member_created",
            tenant_id=tenant_id,
            payload={"team_member_id": str(team_member_id)},
        )


@dataclass
class TeamMemberUpdated(DomainEvent):
    """Emitted after a TeamMember row is patched."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        team_member_id: UUID,
        changed_fields: list[str],
    ) -> TeamMemberUpdated:
        """Build a ``team_member_updated`` event."""
        return cls(
            event_name="team_member_updated",
            tenant_id=tenant_id,
            payload={
                "team_member_id": str(team_member_id),
                "changed_fields": list(changed_fields),
            },
        )


@dataclass
class TeamMemberSoftDeleted(DomainEvent):
    """Emitted after a TeamMember row is soft-deleted."""

    @classmethod
    def create(cls, tenant_id: UUID, team_member_id: UUID) -> TeamMemberSoftDeleted:
        """Build a ``team_member_soft_deleted`` event."""
        return cls(
            event_name="team_member_soft_deleted",
            tenant_id=tenant_id,
            payload={"team_member_id": str(team_member_id)},
        )


# ─────────────────────────────────────────────
# Placement events
# ─────────────────────────────────────────────


@dataclass
class PlacementAdded(DomainEvent):
    """Emitted when a source row is placed on a surface."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        placement_id: UUID,
        source_table: SourceTable,
        source_id: UUID,
        surface_type: SurfaceType,
        surface_ref_id: UUID | None,
    ) -> PlacementAdded:
        """Build a ``placement_added`` event."""
        return cls(
            event_name="placement_added",
            tenant_id=tenant_id,
            payload={
                "placement_id": str(placement_id),
                "source_table": source_table.value,
                "source_id": str(source_id),
                "surface_type": surface_type.value,
                "surface_ref_id": str(surface_ref_id) if surface_ref_id else None,
            },
        )


@dataclass
class PlacementRemoved(DomainEvent):
    """Emitted when a placement is soft-deleted."""

    @classmethod
    def create(cls, tenant_id: UUID, placement_id: UUID) -> PlacementRemoved:
        """Build a ``placement_removed`` event."""
        return cls(
            event_name="placement_removed",
            tenant_id=tenant_id,
            payload={"placement_id": str(placement_id)},
        )


@dataclass
class PlacementReordered(DomainEvent):
    """Emitted when a placement's sort_order or is_visible is updated."""

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        placement_id: UUID,
        changed_fields: list[str],
    ) -> PlacementReordered:
        """Build a ``placement_reordered`` event."""
        return cls(
            event_name="placement_reordered",
            tenant_id=tenant_id,
            payload={
                "placement_id": str(placement_id),
                "changed_fields": list(changed_fields),
            },
        )


__all__ = [
    "AuthorityItemCreated",
    "AuthorityItemSoftDeleted",
    "AuthorityItemUpdated",
    "PlacementAdded",
    "PlacementRemoved",
    "PlacementReordered",
    "TeamMemberCreated",
    "TeamMemberSoftDeleted",
    "TeamMemberUpdated",
    "TestimonialCreated",
    "TestimonialSoftDeleted",
    "TestimonialUpdated",
]
