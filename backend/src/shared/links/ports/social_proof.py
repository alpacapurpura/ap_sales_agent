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

from typing import TYPE_CHECKING, Any

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


# ──────────────────────────────────────────────────────────────
# Pre-serialized convenience helpers for cross-module consumers
# ──────────────────────────────────────────────────────────────
#
# ``resolve_sales_agent_context`` and ``resolve_landing_page_context`` return
# plain ``dict`` bundles already shaped for Jinja templates so the consumer
# module never has to import ``SurfaceType`` or the resolver classes. This
# preserves the DDD boundary — social_proof's domain types stay private.


def resolve_sales_agent_context(db: Session, tenant_id: UUID) -> dict[str, Any]:
    """Return social proof shaped for the Sales Agent identity prompt.

    The agent KB surface is tenant-wide (``surface_ref_id`` is None), but we
    also merge brand-homepage placements via ``include_brand=True`` so the
    agent has everything the public brand page shows plus anything pinned
    explicitly to the SALES_AGENT_KB surface.

    Returns:
        ``{"testimonials": list[dict], "authority_items": list[dict], "team_members": list[dict]}``
        — every entity pre-serialized via ``model_dump(mode="json")``, safe
        to drop into ``prompt_loader.render``.
    """
    from src.modules.social_proof.application.services.social_proof_resolver import (
        SocialProofResolver,
    )
    from src.modules.social_proof.domain.enums import SurfaceType as _Surface

    resolved = SocialProofResolver(db).for_surface(
        tenant_id=tenant_id,
        surface_type=_Surface.SALES_AGENT_KB,
        surface_ref_id=None,
        include_brand=True,
    )
    return {
        "testimonials": [p.testimonial.model_dump(mode="json") for p in resolved.testimonials],
        "authority_items": [p.authority_item.model_dump(mode="json") for p in resolved.authority_items],
        "team_members": [p.team_member.model_dump(mode="json") for p in resolved.team_members],
    }


def resolve_offer_context(
    db: Session,
    tenant_id: UUID,
    offer_id: UUID,
    *,
    include_brand: bool = True,
) -> dict[str, Any]:
    """Return social proof for an offer page, pre-serialized for templates."""
    from src.modules.social_proof.application.services.social_proof_resolver import (
        SocialProofResolver,
    )
    from src.modules.social_proof.domain.enums import SurfaceType as _Surface

    resolved = SocialProofResolver(db).for_surface(
        tenant_id=tenant_id,
        surface_type=_Surface.OFFER,
        surface_ref_id=offer_id,
        include_brand=include_brand,
    )
    return {
        "testimonials": [p.testimonial.model_dump(mode="json") for p in resolved.testimonials],
        "authority_items": [p.authority_item.model_dump(mode="json") for p in resolved.authority_items],
        "team_members": [p.team_member.model_dump(mode="json") for p in resolved.team_members],
    }


def resolve_landing_page_context(
    db: Session,
    tenant_id: UUID,
    landing_page_id: UUID,
    *,
    include_brand: bool = True,
) -> dict[str, Any]:
    """Return social proof for a landing page, pre-serialized for templates."""
    from src.modules.social_proof.application.services.social_proof_resolver import (
        SocialProofResolver,
    )
    from src.modules.social_proof.domain.enums import SurfaceType as _Surface

    resolved = SocialProofResolver(db).for_surface(
        tenant_id=tenant_id,
        surface_type=_Surface.LANDING_PAGE,
        surface_ref_id=landing_page_id,
        include_brand=include_brand,
    )
    return {
        "testimonials": [p.testimonial.model_dump(mode="json") for p in resolved.testimonials],
        "authority_items": [p.authority_item.model_dump(mode="json") for p in resolved.authority_items],
        "team_members": [p.team_member.model_dump(mode="json") for p in resolved.team_members],
    }


# ──────────────────────────────────────────────────────────────
# Extraction sync — brand extraction writes results here
# ──────────────────────────────────────────────────────────────
#
# Brand extraction historically mutated ``BrandSettings.{testimonials,
# authority_vault,team}`` directly. The Brand Studio UI now reads from
# ``/api/v1/social-proof/*`` (new bounded context), so the legacy write is
# invisible to the user. These helpers bridge the gap: after the extraction
# service saves its legacy BrandSettings snapshot, it also upserts the items
# into social_proof via these ports.
#
# Semantics by mode:
#  * ``initial`` — "empezar desde cero": soft-delete existing live items of
#    each kind for the tenant, then create fresh rows from the extraction.
#  * ``update``  — "completar faltantes": create only if the tenant has zero
#    live items of that kind. Avoids duplicates on repeat runs.
#  * ``suggest`` — never writes. Extraction is advisory.


def sync_testimonials_from_extraction(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    mode: str,
    items: list[dict[str, Any]],
) -> int:
    """Write extracted testimonials into the social_proof bounded context.

    Returns the number of newly created testimonials. Swallows and logs
    item-level validation errors — a single bad row never aborts the batch.
    """
    if mode == "suggest" or not items:
        return 0
    from src.modules.social_proof.application.services.testimonial_service import (
        TestimonialService,
    )
    from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
        TestimonialRepository,
    )

    service = TestimonialService(db)
    repo = TestimonialRepository(db)

    if mode == "initial":
        for existing in repo.list_by_tenant(tenant_id, active_only=True):
            service.soft_delete(tenant_id, existing.id)
    elif mode == "update" and repo.list_by_tenant(tenant_id, active_only=True):
        return 0

    created = 0
    for raw in items:
        name = (raw.get("author_name") or raw.get("author") or "").strip()
        if not name:
            continue
        content = (raw.get("content") or raw.get("quote") or "").strip() or None
        media_type = "video" if (raw.get("type") or raw.get("media_type")) == "video" else "text"
        try:
            service.create(
                tenant_id=tenant_id,
                user_id=user_id,
                author_name=name,
                author_role=(raw.get("author_role") or raw.get("role")) or None,
                author_avatar_url=raw.get("author_avatar") or raw.get("avatar_url") or None,
                content=content,
                media_type=media_type,
                rating=raw.get("rating"),
                source_url=raw.get("source_url"),
            )
            created += 1
        except Exception:  # noqa: BLE001 — extraction row quality is best-effort
            import structlog

            structlog.get_logger(__name__).warning(
                "social_proof_sync_testimonial_failed",
                tenant_id=str(tenant_id),
                author=name,
                exc_info=True,
            )
    return created


def sync_authority_items_from_extraction(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    mode: str,
    items: list[dict[str, Any]],
) -> int:
    """Write extracted authority items into the social_proof bounded context.

    The extraction ``type`` field is free text; map it to the closest
    ``AuthorityType`` enum value, falling back to ``OTHER`` when unknown.
    """
    if mode == "suggest" or not items:
        return 0
    from src.modules.social_proof.application.services.authority_service import (
        AuthorityService,
    )
    from src.modules.social_proof.domain.enums import AuthorityType
    from src.modules.social_proof.infrastructure.repositories.authority_item_repository import (
        AuthorityItemRepository,
    )

    service = AuthorityService(db)
    repo = AuthorityItemRepository(db)

    if mode == "initial":
        for existing in repo.list_by_tenant(tenant_id, active_only=True):
            service.soft_delete(tenant_id, existing.id)
    elif mode == "update" and repo.list_by_tenant(tenant_id, active_only=True):
        return 0

    known_types = {t.value for t in AuthorityType}
    created = 0
    for raw in items:
        name = (raw.get("entity_name") or raw.get("title") or "").strip()
        if not name:
            continue
        raw_type = (raw.get("type") or "").strip().lower()
        authority_type = AuthorityType(raw_type) if raw_type in known_types else AuthorityType.OTHER
        try:
            service.create(
                tenant_id=tenant_id,
                user_id=user_id,
                entity_name=name,
                authority_type=authority_type,
                context=raw.get("context"),
                proof_url=raw.get("proof_url") or raw.get("url"),
                logo_url=raw.get("logo_url"),
            )
            created += 1
        except Exception:  # noqa: BLE001 — extraction row quality is best-effort
            import structlog

            structlog.get_logger(__name__).warning(
                "social_proof_sync_authority_failed",
                tenant_id=str(tenant_id),
                entity_name=name,
                exc_info=True,
            )
    return created


def sync_team_members_from_extraction(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    mode: str,
    items: list[dict[str, Any]],
) -> int:
    """Write extracted team members into the social_proof bounded context."""
    if mode == "suggest" or not items:
        return 0
    from src.modules.social_proof.application.services.team_service import (
        TeamService,
    )
    from src.modules.social_proof.infrastructure.repositories.team_member_repository import (
        TeamMemberRepository,
    )

    service = TeamService(db)
    repo = TeamMemberRepository(db)

    if mode == "initial":
        for existing in repo.list_by_tenant(tenant_id):
            service.soft_delete(tenant_id, existing.id)
    elif mode == "update" and repo.list_by_tenant(tenant_id):
        return 0

    created = 0
    for idx, raw in enumerate(items):
        name = (raw.get("name") or "").strip()
        if not name:
            continue
        try:
            service.create(
                tenant_id=tenant_id,
                user_id=user_id,
                name=name,
                role=raw.get("role"),
                bio=raw.get("bio"),
                headshot_url=raw.get("headshot_url"),
                is_primary_voice=bool(raw.get("is_primary_voice")),
                gender=raw.get("gender"),
                communication_style=raw.get("communication_style"),
                personal_website=raw.get("personal_website"),
                personal_linkedin=raw.get("personal_linkedin"),
                personal_instagram=raw.get("personal_instagram"),
                personal_tiktok=raw.get("personal_tiktok"),
                personal_facebook=raw.get("personal_facebook"),
                work_whatsapp=raw.get("work_whatsapp"),
                gallery=raw.get("gallery") or [],
                sort_order=idx,
            )
            created += 1
        except Exception:  # noqa: BLE001 — extraction row quality is best-effort
            import structlog

            structlog.get_logger(__name__).warning(
                "social_proof_sync_team_member_failed",
                tenant_id=str(tenant_id),
                name=name,
                exc_info=True,
            )
    return created
