from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.database import get_db, redis_client
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.analytics.application.services.metrics_service import MetricsService
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO
from src.modules.analytics.application.dto.capture_dto import CaptureDetailDTO
from src.modules.analytics.application.dto.nurture_dto import NurtureDetailDTO
from src.modules.analytics.application.dto.opportunity_dto import OpportunityDetailDTO
from src.modules.analytics.application.dto.sales_dto import SalesDetailDTO
from src.modules.analytics.application.dto.adoption_dto import AdoptionDetailDTO
from src.modules.analytics.application.dto.expansion_dto import ExpansionDetailDTO
from src.modules.analytics.application.dto.evangelization_dto import EvangelizationDetailDTO
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl
from src.modules.offer.application.services.offer_read_port_impl import OfferReadPortImpl

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
    "checkout-init": "shopify",
    "abandoned-cart": "shopify",
    "shopify": "shopify",
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


@router.get("/nurturing", response_model=NurtureDetailDTO)
async def get_nurturing_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Nurturing (Stage 2) detail panel metrics.

    Returns MQL counts, cost per MQL, retargeting and automation channel groups
    with per-group cost breakdown.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    return await service.get_nurturing_metrics(user.tenant_id)


@router.get("/opportunity", response_model=OpportunityDetailDTO)
async def get_opportunity_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Opportunity (Stage 3) detail panel metrics.

    Returns SQL pipeline counts (checkout, meetings, payment links),
    grouped into checkout, payment_links, and qualification groups,
    with bottleneck detection for abandoned cart and meeting no-show rates.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_opportunity_metrics(user.tenant_id, start_date, now)


@router.get("/sales", response_model=SalesDetailDTO)
async def get_sales_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Sales (Stage 4) detail panel metrics.

    Returns revenue broken down by Offer Ladder position with CONVERSION/EXPANSION
    split, tier grouping, subscription new/renewal split, CAC calculation,
    and bottleneck detection.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_sales_metrics(user.tenant_id, start_date, now)


@router.get("/adoption", response_model=AdoptionDetailDTO)
async def get_adoption_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Adoption (Stage 5) detail panel metrics.

    Returns customer health post-purchase: active vs inactive per offer,
    health percentage, Time-to-Value, refunds, and bottleneck alerts.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_adoption_metrics(user.tenant_id, start_date, now)


@router.get("/expansion", response_model=ExpansionDetailDTO)
async def get_expansion_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Expansion (Stage 6) detail panel metrics.

    Returns Net MRR, Avg LTV, Churn Rate, and three offer-grouped
    revenue categories (Retencion, Crecimiento, Cancelaciones)
    with bottleneck detection for high churn rates.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_expansion_metrics(user.tenant_id, start_date, now)


@router.get("/evangelization", response_model=EvangelizationDetailDTO)
async def get_evangelization_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Evangelization (Stage 7) detail panel metrics.

    Returns K-Factor, referral conversions, NPS score, evangelist profiles,
    evangelist candidates (NPS >= 9), UGC count, and bottleneck detection.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=30)
    return await service.get_evangelization_metrics(user.tenant_id, start_date, now)


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


_VALID_PROVIDERS = {"meta", "google_analytics", "google_ads", "shopify"}


@router.post("/{provider}/initial-load")
async def trigger_initial_load(
    provider: str,
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Load historical metrics day-by-day for any provider, skipping already-loaded days.

    Idempotent: repeated calls only fetch missing days.
    Applies same 15-min cooldown as channel refresh.
    """
    if provider not in _VALID_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    # Cooldown check
    from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
        ExtractionRunRepository,
    )

    run_repo = ExtractionRunRepository(db)
    latest_run = run_repo.get_latest(user.tenant_id, provider)

    if latest_run and latest_run.started_at:
        elapsed = datetime.now(timezone.utc) - latest_run.started_at
        if elapsed < _REFRESH_COOLDOWN:
            remaining = _REFRESH_COOLDOWN - elapsed
            remaining_min = int(remaining.total_seconds() // 60) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Disponible en {remaining_min} min",
            )

    from src.modules.analytics.application.services.etl_service import ETLService

    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    etl = ETLService(db, connection_port=connection_port, cache=cache)

    try:
        result = await etl.run_initial_load(user.tenant_id, provider, days=days)
        return {
            "status": "ok",
            "total_days": result["total"],
            "loaded_days": result["loaded"],
            "skipped_days": result["skipped"],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Initial load failed: {str(exc)}",
        )


@router.get("/{provider}/initial-load/status")
async def get_initial_load_status(
    provider: str,
    user: User = Depends(get_current_user),
):
    """Check progress of an initial load (reads from Redis)."""
    if provider not in _VALID_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")

    import json

    progress_key = f"initial_load:{user.tenant_id}:{provider}"
    raw = redis_client.get(progress_key) if redis_client else None

    if not raw:
        return {"status": "idle"}

    try:
        data = json.loads(raw)
        return data
    except (json.JSONDecodeError, TypeError):
        return {"status": "idle"}
