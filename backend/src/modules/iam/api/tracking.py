from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.tracking_config import TrackingConfig
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models.tenant_model import TenantModel

logger = structlog.get_logger()

router = APIRouter()
public_router = APIRouter()


@router.get("/tracking", response_model=TrackingConfig, summary="Get tracking config")
async def get_tracking_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TrackingConfig:
    """Get current tracking configuration for the tenant."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=400, detail="User is not associated with a tenant"
        )

    result = db.execute(select(TenantModel).where(TenantModel.id == user.tenant_id))
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    logger.info("tracking_config_fetched", tenant_id=str(user.tenant_id))
    return TrackingConfig(**(tenant.tracking_config or {}))


@router.patch(
    "/tracking", response_model=TrackingConfig, summary="Update tracking config"
)
async def update_tracking_config(
    config: TrackingConfig,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TrackingConfig:
    """Update GTM, Meta Pixel, GA4 tracking configuration for the tenant."""
    if not user.tenant_id:
        raise HTTPException(
            status_code=400, detail="User is not associated with a tenant"
        )

    result = db.execute(select(TenantModel).where(TenantModel.id == user.tenant_id))
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Merge: only update non-None fields (preserve existing values)
    existing = tenant.tracking_config or {}
    merged = {**existing, **config.model_dump(exclude_none=True)}
    tenant.tracking_config = merged
    db.commit()
    db.refresh(tenant)

    logger.info("tracking_config_updated", tenant_id=str(user.tenant_id))
    return TrackingConfig(**(tenant.tracking_config or {}))


@public_router.get(
    "/tracking/{tenant_id}",
    response_model=TrackingConfig,
    summary="Public tracking config",
)
async def get_public_tracking_config(
    tenant_id: UUID,
    db: Session = Depends(get_db),
) -> TrackingConfig:
    """
    Public endpoint: returns tracking config for a tenant.
    Called by public site layout to inject GTM/Pixel scripts.
    """
    result = db.execute(select(TenantModel).where(TenantModel.id == tenant_id))
    tenant = result.scalars().first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TrackingConfig(**(tenant.tracking_config or {}))
