"""SQLAlchemy models for the social_proof bounded context.

Importing this package registers the 4 tables on the shared ``Base`` metadata
so Alembic autogenerate (if ever enabled) and tests using ``Base.metadata``
can see them.
"""

from luana_core_social_proof.infrastructure.models.authority_item_model import (
    AuthorityItemModel,
)
from luana_core_social_proof.infrastructure.models.placement_model import (
    PlacementModel,
)
from luana_core_social_proof.infrastructure.models.team_member_model import (
    TeamMemberModel,
)
from luana_core_social_proof.infrastructure.models.testimonial_model import (
    TestimonialModel,
)

__all__ = [
    "AuthorityItemModel",
    "PlacementModel",
    "TeamMemberModel",
    "TestimonialModel",
]
