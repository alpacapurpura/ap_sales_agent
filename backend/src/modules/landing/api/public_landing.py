"""Public landing page endpoint — no auth required.

Accessible at: GET /api/v1/public/landing/{slug}

The X-Tenant-ID header is required. In Phase 1 it will be injected by the
Cloudflare Worker that resolves custom domains. Until then clients must
supply it explicitly.
"""
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.landing.infrastructure.repositories.landing_repository import LandingRepository

logger = structlog.get_logger()

router = APIRouter()


# ---------------------------------------------------------------------------
# Response DTO
# ---------------------------------------------------------------------------


class PublicLandingResponse(BaseModel):
    """Public-safe representation of a landing page.

    All fields are deliberately non-PII. The full config (visual structure,
    copy) is returned so the frontend renderer can display the page without
    additional requests.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    offer_id: Optional[UUID] = None
    slug: str
    config: LandingPageConfig
    is_published: bool


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.get(
    "/landing/{slug}",
    response_model=PublicLandingResponse,
    summary="Get a published landing page by slug (public)",
    tags=["Public - Landing"],
)
def get_public_landing(
    slug: str,
    x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-ID"),
    db: Session = Depends(get_db),
) -> PublicLandingResponse:
    """Return a landing page by slug scoped to the given tenant.

    - Returns 400 if X-Tenant-ID header is missing.
    - Returns 404 if the slug does not exist for that tenant or is not published.
    """
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header is required")

    try:
        tenant_uuid = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Tenant-ID must be a valid UUID")

    repo = LandingRepository(db)
    landing = repo.get_by_slug_and_tenant(slug=slug, tenant_id=tenant_uuid)

    if not landing:
        logger.info(
            "public_landing_not_found",
            slug=slug,
            tenant_id=x_tenant_id,
        )
        raise HTTPException(status_code=404, detail="Landing page not found")

    if not landing.is_published:
        # Only the tenant owner can preview unpublished landings — this public
        # endpoint only serves published content.
        logger.info(
            "public_landing_not_published",
            slug=slug,
            tenant_id=x_tenant_id,
            landing_id=str(landing.id),
        )
        raise HTTPException(status_code=404, detail="Landing page not found")

    logger.info(
        "public_landing_served",
        slug=slug,
        tenant_id=x_tenant_id,
        landing_id=str(landing.id),
    )
    return PublicLandingResponse(
        id=landing.id,
        tenant_id=landing.tenant_id,
        offer_id=landing.offer_id,
        slug=landing.slug,
        config=landing.config,
        is_published=landing.is_published,
    )
