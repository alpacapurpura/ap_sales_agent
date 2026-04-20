"""Cross-module port for social_proof.

Other bounded contexts (sales_agent, landing, offer, copilot) MUST consume
these functions instead of importing from ``social_proof/`` directly. Lazy
imports inside each function prevent circular imports and keep ``shared/``
dependency-free from ``modules/`` at import time.

Design:
  * All reads are tenant-scoped — callers pass ``tenant_id`` explicitly.
  * The two main entry points are:
      - ``resolve_for_surface`` — "dame todo lo que se ve en X".
      - ``list_tenant_catalog`` — "dame el catálogo completo del tenant"
        (used by Copilot when suggesting items to link).
  * Return objects are the rich domain entities + ``PlacedXxx`` bundles —
    callers can pick the subset they need.

Consumers:
  - ``sales_agent`` — grounding the agent knowledge base with testimonials
    and authority items.
  - ``landing`` — populating landing pages with tenant-scoped social proof.
  - ``offer`` — fetching per-offer placements for the Offer editor + public
    offer pages.
  - ``copilot`` — schema introspection and suggestion tools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.social_proof.application.services.social_proof_resolver import (
        ResolvedSocialProof,
    )
    from src.modules.social_proof.domain.authority_item import AuthorityItem
    from src.modules.social_proof.domain.enums import SurfaceType
    from src.modules.social_proof.domain.team_member import TeamMember
    from src.modules.social_proof.domain.testimonial import Testimonial


def resolve_for_surface(
    db: Session,
    tenant_id: UUID,
    surface_type: SurfaceType,
    surface_ref_id: UUID | None,
    *,
    include_brand: bool = False,
) -> ResolvedSocialProof:
    """Return every live, visible social-proof item on the given surface.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: Tenant scope (enforced at the repository).
        surface_type: ``offer`` / ``landing_page`` / ``email_sequence`` /
            ``brand_homepage`` / ``sales_agent_kb``.
        surface_ref_id: PK of the concrete surface row; ``None`` for
            tenant-wide surfaces (brand_homepage, sales_agent_kb).
        include_brand: When True and ``surface_type`` is not
            ``brand_homepage``, merge the tenant's brand-level placements
            so callers get the fallback for free.

    Returns:
        A :class:`ResolvedSocialProof` bundle with ``testimonials``,
        ``authority_items`` and ``team_members``.
    """
    from src.modules.social_proof.application.services.social_proof_resolver import (
        SocialProofResolver,
    )

    return SocialProofResolver(db).for_surface(
        tenant_id=tenant_id,
        surface_type=surface_type,
        surface_ref_id=surface_ref_id,
        include_brand=include_brand,
    )


def list_tenant_testimonials(
    db: Session,
    tenant_id: UUID,
) -> list[Testimonial]:
    """Return every live testimonial for the tenant (full catalog)."""
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )

    return TestimonialRepository(db).list_by_tenant(tenant_id)


def list_tenant_authority_items(
    db: Session,
    tenant_id: UUID,
) -> list[AuthorityItem]:
    """Return every live authority item for the tenant."""
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )

    return AuthorityItemRepository(db).list_by_tenant(tenant_id)


def list_tenant_team_members(
    db: Session,
    tenant_id: UUID,
) -> list[TeamMember]:
    """Return every live team member for the tenant (ordered by sort_order)."""
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )

    return TeamMemberRepository(db).list_by_tenant(tenant_id)
