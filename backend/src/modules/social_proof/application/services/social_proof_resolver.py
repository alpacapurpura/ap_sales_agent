"""Read model for the hot "for_surface" query.

Callers ask: "give me every testimonial / authority / team_member that is
visible on surface X". The resolver collapses the Placement + source-row
lookup into a single, batched read so the caller never issues N+1 queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.modules.social_proof.domain.authority_item import AuthorityItem
from src.modules.social_proof.domain.enums import SourceTable, SurfaceType
from src.modules.social_proof.domain.placement import Placement
from src.modules.social_proof.domain.team_member import TeamMember
from src.modules.social_proof.domain.testimonial import Testimonial
from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
    AuthorityItemRepository,
)
from src.modules.social_proof.infrastructure.repositories.placement_repository import (
    PlacementRepository,
)
from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
    TeamMemberRepository,
)
from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
    TestimonialRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


@dataclass
class PlacedTestimonial:
    """Testimonial alongside its placement — preserves surface-specific sort order."""

    testimonial: Testimonial
    placement: Placement


@dataclass
class PlacedAuthorityItem:
    """AuthorityItem alongside its placement."""

    authority_item: AuthorityItem
    placement: Placement


@dataclass
class PlacedTeamMember:
    """TeamMember alongside its placement."""

    team_member: TeamMember
    placement: Placement


@dataclass
class ResolvedSocialProof:
    """Full bundle for a surface — what the dashboard or landing renders."""

    testimonials: list[PlacedTestimonial]
    authority_items: list[PlacedAuthorityItem]
    team_members: list[PlacedTeamMember]


class SocialProofResolver:
    """Efficient read model — batched lookup for a surface."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db
        self.placements = PlacementRepository(db)
        self.testimonials = TestimonialRepository(db)
        self.authority = AuthorityItemRepository(db)
        self.team = TeamMemberRepository(db)

    def for_surface(
        self,
        *,
        tenant_id: UUID,
        surface_type: SurfaceType,
        surface_ref_id: UUID | None,
        include_brand: bool = False,
    ) -> ResolvedSocialProof:
        """Return every live, visible social-proof item on the surface.

        Args:
            tenant_id: Required tenant scope.
            surface_type: ``offer`` / ``landing_page`` / ``email_sequence`` /
                ``brand_homepage`` / ``sales_agent_kb``.
            surface_ref_id: PK of the surface row (None for brand-wide).
            include_brand: When ``True`` and the surface is non-brand, also
                pull the tenant's ``brand_homepage`` placements. Useful for
                "fall back to brand defaults if the offer has no overrides".
        """
        surface_placements = self.placements.list_for_surface(
            tenant_id=tenant_id,
            surface_type=surface_type,
            surface_ref_id=surface_ref_id,
        )

        if include_brand and surface_type is not SurfaceType.BRAND_HOMEPAGE:
            brand_placements = self.placements.list_for_surface(
                tenant_id=tenant_id,
                surface_type=SurfaceType.BRAND_HOMEPAGE,
                surface_ref_id=None,
            )
            # Surface-specific placements take precedence — do not duplicate
            # the same source row when it already has a direct placement.
            direct_keys = {(p.source_table, p.source_id) for p in surface_placements}
            merged_placements = list(surface_placements) + [
                p for p in brand_placements if (p.source_table, p.source_id) not in direct_keys
            ]
        else:
            merged_placements = list(surface_placements)

        testimonial_ids = [p.source_id for p in merged_placements if p.source_table is SourceTable.TESTIMONIAL]
        authority_ids = [p.source_id for p in merged_placements if p.source_table is SourceTable.AUTHORITY_ITEM]
        team_ids = [p.source_id for p in merged_placements if p.source_table is SourceTable.TEAM_MEMBER]

        testimonial_map = {t.id: t for t in self.testimonials.list_by_ids(tenant_id, testimonial_ids)}
        authority_map = {a.id: a for a in self.authority.list_by_ids(tenant_id, authority_ids)}
        team_map = {m.id: m for m in self.team.list_by_ids(tenant_id, team_ids)}

        testimonials_out: list[PlacedTestimonial] = []
        authority_out: list[PlacedAuthorityItem] = []
        team_out: list[PlacedTeamMember] = []

        for placement in merged_placements:
            if placement.source_table is SourceTable.TESTIMONIAL:
                entity = testimonial_map.get(placement.source_id)
                if entity is not None:
                    testimonials_out.append(
                        PlacedTestimonial(testimonial=entity, placement=placement),
                    )
            elif placement.source_table is SourceTable.AUTHORITY_ITEM:
                entity_a = authority_map.get(placement.source_id)
                if entity_a is not None:
                    authority_out.append(
                        PlacedAuthorityItem(authority_item=entity_a, placement=placement),
                    )
            elif placement.source_table is SourceTable.TEAM_MEMBER:
                entity_t = team_map.get(placement.source_id)
                if entity_t is not None:
                    team_out.append(PlacedTeamMember(team_member=entity_t, placement=placement))

        return ResolvedSocialProof(
            testimonials=testimonials_out,
            authority_items=authority_out,
            team_members=team_out,
        )
