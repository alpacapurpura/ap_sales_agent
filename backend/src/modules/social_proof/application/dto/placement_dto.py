"""Request / Response DTOs for the Placement API + resolver output."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.social_proof.application.dto.authority_dto import AuthorityResponseDTO
from src.modules.social_proof.application.dto.team_dto import TeamMemberResponseDTO
from src.modules.social_proof.application.dto.testimonial_dto import (
    TestimonialResponseDTO,
)
from src.modules.social_proof.domain.enums import SourceTable, SurfaceType


class PlacementCreateDTO(BaseModel):
    """POST body — link an existing source row to a surface."""

    source_table: SourceTable
    source_id: UUID
    surface_type: SurfaceType
    surface_ref_id: UUID | None = None
    sort_order: int = 0
    is_visible: bool = True


class PlacementUpdateDTO(BaseModel):
    """PATCH body — reorder or toggle visibility."""

    sort_order: int | None = None
    is_visible: bool | None = None


class PlacementResponseDTO(BaseModel):
    """Full placement payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    source_table: SourceTable
    source_id: UUID
    surface_type: SurfaceType
    surface_ref_id: UUID | None
    sort_order: int
    is_visible: bool
    created_at: datetime | None
    updated_at: datetime | None


class PlacedTestimonialDTO(BaseModel):
    """Testimonial + placement bundle (resolver output)."""

    testimonial: TestimonialResponseDTO
    placement: PlacementResponseDTO


class PlacedAuthorityItemDTO(BaseModel):
    """AuthorityItem + placement bundle (resolver output)."""

    authority_item: AuthorityResponseDTO
    placement: PlacementResponseDTO


class PlacedTeamMemberDTO(BaseModel):
    """TeamMember + placement bundle (resolver output)."""

    team_member: TeamMemberResponseDTO
    placement: PlacementResponseDTO


class ResolvedSocialProofDTO(BaseModel):
    """Full "for-surface" response — what a surface renders."""

    testimonials: list[PlacedTestimonialDTO] = Field(default_factory=list)
    authority_items: list[PlacedAuthorityItemDTO] = Field(default_factory=list)
    team_members: list[PlacedTeamMemberDTO] = Field(default_factory=list)
