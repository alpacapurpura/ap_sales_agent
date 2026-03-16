from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db, redis_client
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.analytics.application.services.metrics_service import MetricsService
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO
from src.modules.analytics.application.dto.capture_dto import CaptureDetailDTO
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl

router = APIRouter(prefix="/metrics", tags=["Marketing Metrics"])

# Refresh cooldown: 15 minutes
_REFRESH_COOLDOWN = timedelta(minutes=15)

# Map channel slugs to their provider names for refresh routing
_SLUG_TO_PROVIDER: dict[str, str] = {
    "ig-organic": "meta",
    "fb-organic": "meta",
    "meta-ads": "meta",
    "yt-organic": "youtube",
    "yt-ads": "google_ads",
    "tiktok-organic": "tiktok",
    "tiktok-ads": "tiktok",
    "google-organic": "google_analytics",
    "direct": "google_analytics",
    "ai-search-organic": "google_analytics",
    "google-ads": "google_ads",
    "cold-contact": "manual",
}


@router.get("/sankey")
async def get_marketing_sankey(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get Marketing Sankey Metrics (7 Nodes).
    """
    service = MetricsService(db)
    return service.get_marketing_sankey_metrics(user.tenant_id)


@router.get("/attraction", response_model=AttractionDetailDTO)
async def get_attraction_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get Attraction stage metrics with dynamic channel list from ETL tables.
    Channels are sourced from ChannelRegistry; values from official_metrics.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    return await service.get_attraction_metrics(user.tenant_id)


@router.get("/capture", response_model=CaptureDetailDTO)
async def get_capture_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Capture (Stage 1) detail panel metrics.

    Returns lead counts by channel, grouped into web_infrastructure and ai_agent,
    with cost per lead and conversion rate from Stage 0.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    return await service.get_capture_metrics(user.tenant_id)


@router.post("/attraction/refresh/{channel_slug}")
async def refresh_channel_metrics(
    channel_slug: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger re-extraction for a single channel's provider.

    Applies a 15-minute cooldown per provider+tenant to prevent abuse.
    Returns 429 if cooldown is still active.
    """
    provider_name = _SLUG_TO_PROVIDER.get(channel_slug)
    if provider_name is None:
        raise HTTPException(status_code=404, detail=f"Unknown channel: {channel_slug}")

    if provider_name == "manual":
        raise HTTPException(
            status_code=400,
            detail="Manual channels cannot be refreshed via API",
        )

    # Check cooldown: last extraction run for this provider+tenant
    from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
        ExtractionRunRepository,
    )

    run_repo = ExtractionRunRepository(db)
    latest_run = run_repo.get_latest(user.tenant_id, provider_name)

    if latest_run and latest_run.started_at:
        elapsed = datetime.now(timezone.utc) - latest_run.started_at
        if elapsed < _REFRESH_COOLDOWN:
            remaining = _REFRESH_COOLDOWN - elapsed
            remaining_min = int(remaining.total_seconds() // 60) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Disponible en {remaining_min} min",
            )

    # Trigger extraction
    from src.modules.analytics.application.services.etl_service import ETLService

    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    etl = ETLService(db, connection_port=connection_port, cache=cache)

    try:
        run = await etl.run_extraction(user.tenant_id, provider_name)
        return {
            "status": "ok",
            "run_id": str(run.id),
            "provider": provider_name,
            "channel_slug": channel_slug,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {str(exc)}",
        )
