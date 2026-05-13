"""Repositories for the social_proof bounded context."""

from luana_core_social_proof.infrastructure.repositories.authority_item_repository import (
    AuthorityItemRepository,
)
from luana_core_social_proof.infrastructure.repositories.placement_repository import (
    PlacementRepository,
)
from luana_core_social_proof.infrastructure.repositories.team_member_repository import (
    TeamMemberRepository,
)
from luana_core_social_proof.infrastructure.repositories.testimonial_repository import (
    TestimonialRepository,
)

__all__ = [
    "AuthorityItemRepository",
    "PlacementRepository",
    "TeamMemberRepository",
    "TestimonialRepository",
]
