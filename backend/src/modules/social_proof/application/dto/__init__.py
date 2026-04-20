"""DTOs for the social_proof API layer."""

from src.modules.social_proof.application.dto.authority_dto import (
    AuthorityCreateDTO,
    AuthorityResponseDTO,
    AuthorityUpdateDTO,
)
from src.modules.social_proof.application.dto.placement_dto import (
    PlacedAuthorityItemDTO,
    PlacedTeamMemberDTO,
    PlacedTestimonialDTO,
    PlacementCreateDTO,
    PlacementResponseDTO,
    PlacementUpdateDTO,
    ResolvedSocialProofDTO,
)
from src.modules.social_proof.application.dto.team_dto import (
    TeamMemberCreateDTO,
    TeamMemberResponseDTO,
    TeamMemberUpdateDTO,
)
from src.modules.social_proof.application.dto.testimonial_dto import (
    TestimonialCreateDTO,
    TestimonialResponseDTO,
    TestimonialUpdateDTO,
)

__all__ = [
    "AuthorityCreateDTO",
    "AuthorityResponseDTO",
    "AuthorityUpdateDTO",
    "PlacedAuthorityItemDTO",
    "PlacedTeamMemberDTO",
    "PlacedTestimonialDTO",
    "PlacementCreateDTO",
    "PlacementResponseDTO",
    "PlacementUpdateDTO",
    "ResolvedSocialProofDTO",
    "TeamMemberCreateDTO",
    "TeamMemberResponseDTO",
    "TeamMemberUpdateDTO",
    "TestimonialCreateDTO",
    "TestimonialResponseDTO",
    "TestimonialUpdateDTO",
]
