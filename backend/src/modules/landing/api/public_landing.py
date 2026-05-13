"""Public landing page endpoint — no auth required.

Accessible at: GET /api/v1/public/landing/{slug}

The X-Tenant-ID header is required. In Phase 1 it will be injected by the
Cloudflare Worker that resolves custom domains. Until then clients must
supply it explicitly.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from luana_core_landing.application.landing_service import LandingService
from luana_core_landing.domain.content import LandingPageConfig
from luana_core_platform.core.database import get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

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
    tenant_id is intentionally excluded — unnecessary info disclosure on a
    public unauthenticated endpoint.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID | None = None
    slug: str
    config: LandingPageConfig
    is_published: bool


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

# NOTE: This module uses synchronous SQLAlchemy (Session, not AsyncSession).
# The entire landing module predates the async migration — tracked as tech debt.
# Do NOT add async/await here until database.py is upgraded to async engine.


@router.get(
    "/landing/{slug}",
    summary="Get a published landing page by slug (public)",
    tags=["Public - Landing"],
)
def get_public_landing(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
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
        raise HTTPException(
            status_code=400,
            detail="X-Tenant-ID must be a valid UUID",
        ) from None

    service = LandingService(db)
    landing = service.get_public_landing(slug=slug, tenant_id=tenant_uuid)

    if not landing:
        logger.info(
            "public_landing_not_found",
            slug=slug,
            tenant_id=x_tenant_id,
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
        offer_id=landing.offer_id,
        slug=landing.slug,
        config=landing.config,
        is_published=landing.is_published,
    )
