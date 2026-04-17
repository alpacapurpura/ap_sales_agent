"""Public per-edition landing resolver (Phase 8).

Two public routes, no auth:

- ``GET /public/tenants/{tenant_slug}/offers/{offer_id}``
    Resolves the offer's "next available" edition (ACTIVE preferred, else
    soonest UPCOMING + PUBLIC) and issues a ``302`` redirect to the
    edition-scoped path.

- ``GET /public/tenants/{tenant_slug}/offers/{offer_id}/ediciones/{edition_number}``
    Returns the landing for that specific (offer, edition) pair, scoped to
    the tenant resolved from slug. Falls back to the offer-level landing
    template if the edition does not have its own landing yet.

Tenant slug → tenant UUID is resolved via ``iam.tenants.slug``.
Offer slugs don't exist yet in the model — the URL uses ``offer_id``
(UUID) as a placeholder. Migrating to real slugs is tracked separately.
"""

from typing import Annotated, Any
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.landing.api.public_landing import PublicLandingResponse
from src.modules.landing.application.landing_service import LandingService
from src.modules.landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)
from src.shared.links.ports.offer import get_launch_edition_repository

logger = structlog.get_logger()

router = APIRouter()


def _resolve_tenant_id(db: Session, tenant_slug: str) -> UUID:
    stmt = select(TenantModel.id).where(TenantModel.slug == tenant_slug)
    tenant_id = db.execute(stmt).scalar_one_or_none()
    if tenant_id is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant_id


def _pick_active_edition(editions: list[Any]) -> Any | None:  # noqa: ANN401 — duck-typed domain object
    """Return the edition we want a public URL to point at.

    Preference: currently ACTIVE > nearest UPCOMING > None. Editions are
    expected to already be PUBLIC (the repo's ``list_public`` filter).
    Compares against the StrEnum's string value to avoid a direct import
    of the offer domain (enforced by arch test ``test_no_new_cross_module_imports``).
    """
    active = next((e for e in editions if getattr(e.status, "value", e.status) == "active"), None)
    if active:
        return active
    upcoming = [e for e in editions if getattr(e.status, "value", e.status) == "upcoming" and e.start_date]
    if upcoming:
        return sorted(upcoming, key=lambda e: e.start_date)[0]
    return None


@router.get(
    "/tenants/{tenant_slug}/offers/{offer_id}",
    tags=["Public - Landing"],
    summary="Redirect to the offer's currently-active edition landing",
)
def redirect_to_active_edition(
    tenant_slug: str,
    offer_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> RedirectResponse:
    """302 to ``/public/tenants/{slug}/offers/{offer}/ediciones/{n}`` or 404."""
    tenant_id = _resolve_tenant_id(db, tenant_slug)
    edition_repo = get_launch_edition_repository(db)
    editions = edition_repo.list_public(offer_id, tenant_id)
    pick = _pick_active_edition(editions)
    if pick is None:
        raise HTTPException(status_code=404, detail="No public edition for this offer")
    return RedirectResponse(
        url=f"/api/v1/public/tenants/{tenant_slug}/offers/{offer_id}/ediciones/{pick.edition_number}",
        status_code=302,
    )


@router.get(
    "/tenants/{tenant_slug}/offers/{offer_id}/ediciones/{edition_number}",
    tags=["Public - Landing"],
    summary="Serve the landing for a specific (offer, edition) pair",
)
def get_edition_landing(
    tenant_slug: str,
    offer_id: UUID,
    edition_number: int,
    db: Annotated[Session, Depends(get_db)],
) -> PublicLandingResponse:
    """Return landing scoped to ``(offer_id, edition_number)``.

    Falls back to the offer-level landing template if the edition has no
    landing of its own yet. Always tenant-scoped.
    """
    tenant_id = _resolve_tenant_id(db, tenant_slug)

    edition_repo = get_launch_edition_repository(db)
    editions = edition_repo.list_by_offer(offer_id, tenant_id)
    edition = next(
        (e for e in editions if e.edition_number == edition_number),
        None,
    )
    if edition is None:
        raise HTTPException(status_code=404, detail="Edition not found")

    service = LandingService(db)
    repo = LandingRepository(db)
    landing = repo.get_by_offer_and_edition(tenant_id, offer_id, edition.id)
    if landing is None:
        # Fallback to offer-level (null edition_id) template.
        landing = repo.get_by_offer_and_edition(tenant_id, offer_id, None)
    if landing is None or not landing.is_published:
        raise HTTPException(status_code=404, detail="Landing not published")

    # Service does not expose a plain getter, but the read path above suffices.
    _ = service  # keep import for future enrichment (open graph, theming)
    return PublicLandingResponse(
        id=landing.id,
        offer_id=landing.offer_id,
        slug=landing.slug,
        config=landing.config,
        is_published=landing.is_published,
    )
