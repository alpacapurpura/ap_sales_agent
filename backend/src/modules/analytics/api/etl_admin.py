"""ETL admin and health endpoints for monitoring the extraction pipeline.

Provides:
- GET /health/etl: Health check (no auth) showing last run, pending, failures
- POST /etl/retry/{run_id}: Manual retry with 15-min cooldown (requires tenant context)
- GET /etl/status: Per-provider extraction status for a tenant (requires tenant context)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.analytics.domain.enums import ExtractionStatus
from src.modules.analytics.infrastructure.models.extraction_run_model import (
    ExtractionRunModel,
)

logger = logging.getLogger(__name__)

# --- Response Models ---


class ActiveFailure(BaseModel):
    """Represent active failure data."""

    tenant_id: str
    provider: str
    error: str | None = None
    failed_at: datetime | None = None


class ETLHealthResponse(BaseModel):
    """Response schema for e t l health."""

    last_successful_run: datetime | None = None
    pending_tenants: int = 0
    active_failures: list[ActiveFailure] = []
    timestamp: datetime


class RetryResponse(BaseModel):
    """Response schema for retry."""

    status: str
    run_id: str


class SubExtractorFailureDTO(BaseModel):
    """Data transfer object for sub extractor failure."""

    extractor_name: str
    error: str
    error_type: str


class ExtractionStatusItem(BaseModel):
    """Represent extraction status item data."""

    provider: str
    status: str
    last_updated: datetime | None = None
    error: str | None = None
    metrics_count: int = 0
    sub_extractor_failures: list[SubExtractorFailureDTO] = []


class ETLStatusResponse(BaseModel):
    """Response schema for e t l status."""

    tenant_id: str
    extractions: list[ExtractionStatusItem]


# --- Routers ---

# Health router (no auth required)
health_router = APIRouter()

# Tenant-scoped router (requires X-Tenant-ID)
tenant_router = APIRouter()


@health_router.get("/health/etl")
def get_etl_health(db: Annotated[Session, Depends(get_db)]) -> ETLHealthResponse:
    """Return ETL pipeline health status.

    No authentication required — this is a health endpoint.
    """
    # Last successful run across all tenants
    last_success_stmt = (
        select(ExtractionRunModel.completed_at)
        .where(ExtractionRunModel.status == ExtractionStatus.SUCCESS.value)
        .order_by(ExtractionRunModel.completed_at.desc())
        .limit(1)
    )
    last_success = db.execute(last_success_stmt).scalar_one_or_none()

    # Pending tenants (distinct tenant_ids with PENDING or RUNNING status)
    pending_stmt = select(
        func.count(func.distinct(ExtractionRunModel.tenant_id)),
    ).where(
        ExtractionRunModel.status.in_(
            [
                ExtractionStatus.PENDING.value,
                ExtractionStatus.RUNNING.value,
            ],
        ),
    )
    pending_count = db.execute(pending_stmt).scalar_one() or 0

    # Active failures (latest failed runs)
    failed_stmt = (
        select(ExtractionRunModel)
        .where(ExtractionRunModel.status == ExtractionStatus.FAILED.value)
        .order_by(ExtractionRunModel.created_at.desc())
        .limit(20)
    )
    failed_runs = db.execute(failed_stmt).scalars().all()

    active_failures = [
        ActiveFailure(
            tenant_id=str(run.tenant_id),
            provider=run.provider,
            error=run.error,
            failed_at=run.completed_at,
        )
        for run in failed_runs
    ]

    return ETLHealthResponse(
        last_successful_run=last_success,
        pending_tenants=pending_count,
        active_failures=active_failures,
        timestamp=datetime.now(UTC),
    )


@tenant_router.post("/etl/retry/{run_id}")
async def retry_extraction(
    run_id: UUID,
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    db: Annotated[Session, Depends(get_db)],
) -> RetryResponse:
    """Manually retry a failed extraction run.

    Enforces a 15-minute cooldown between retry attempts for the same
    tenant+provider combination.
    """
    tenant_id = UUID(x_tenant_id)

    # Find the failed run
    stmt = select(ExtractionRunModel).where(
        ExtractionRunModel.id == run_id,
        ExtractionRunModel.tenant_id == tenant_id,
    )
    run = db.execute(stmt).scalars().first()

    if run is None:
        raise HTTPException(status_code=404, detail="Extraction run not found")

    # Cooldown check: no retry within 15 minutes for same tenant+provider
    cooldown_threshold = datetime.now(UTC) - timedelta(minutes=15)
    recent_stmt = (
        select(ExtractionRunModel)
        .where(
            ExtractionRunModel.tenant_id == tenant_id,
            ExtractionRunModel.provider == run.provider,
            ExtractionRunModel.status.in_(
                [
                    ExtractionStatus.PENDING.value,
                    ExtractionStatus.RUNNING.value,
                    ExtractionStatus.RETRYING.value,
                ],
            ),
            ExtractionRunModel.created_at > cooldown_threshold,
        )
        .limit(1)
    )
    recent = db.execute(recent_stmt).scalars().first()

    if recent is not None:
        raise HTTPException(
            status_code=429,
            detail="Retry cooldown active. Please wait 15 minutes between retries.",
        )

    # Enqueue the retry job via ARQ
    try:
        from arq.connections import RedisSettings, create_pool

        from src.core.config import settings

        pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await pool.enqueue_job(
            "run_tenant_extraction",
            str(tenant_id),
            run.provider,
        )
        await pool.close()
    except Exception as exc:
        logger.exception("Failed to enqueue retry job")
        raise HTTPException(
            status_code=500,
            detail="Failed to enqueue retry job",
        ) from exc

    logger.info(
        "Manual retry enqueued for tenant=%s provider=%s run_id=%s",
        tenant_id,
        run.provider,
        run_id,
    )

    return RetryResponse(status="queued", run_id=str(run_id))


@tenant_router.get("/etl/status")
def get_etl_status(
    x_tenant_id: Annotated[str, Header(alias="X-Tenant-ID")],
    db: Annotated[Session, Depends(get_db)],
) -> ETLStatusResponse:
    """Return the latest extraction run per provider for the tenant.

    Used by the frontend for the "Ultima actualizacion" display.
    """
    tenant_id = UUID(x_tenant_id)

    # Get the latest run for each provider using a subquery
    subquery = (
        select(
            ExtractionRunModel.provider,
            func.max(ExtractionRunModel.created_at).label("max_created"),
        )
        .where(ExtractionRunModel.tenant_id == tenant_id)
        .group_by(ExtractionRunModel.provider)
        .subquery()
    )

    stmt = select(ExtractionRunModel).join(
        subquery,
        (ExtractionRunModel.provider == subquery.c.provider)
        & (ExtractionRunModel.created_at == subquery.c.max_created)
        & (ExtractionRunModel.tenant_id == tenant_id),
    )
    runs = db.execute(stmt).scalars().all()

    extractions = [
        ExtractionStatusItem(
            provider=run.provider,
            status=run.status,
            last_updated=run.completed_at or run.created_at,
            error=run.error if run.status == ExtractionStatus.FAILED.value else None,
            metrics_count=run.metrics_count or 0,
            sub_extractor_failures=[
                SubExtractorFailureDTO(
                    extractor_name=f["extractor_name"],
                    error=f["error"],
                    error_type=f["error_type"],
                )
                for f in (run.sub_extractor_failures or [])
            ],
        )
        for run in runs
    ]

    return ETLStatusResponse(
        tenant_id=str(tenant_id),
        extractions=extractions,
    )


# Combined router for easy import
router = APIRouter()
router.include_router(health_router)
router.include_router(tenant_router)
