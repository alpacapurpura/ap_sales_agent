from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db, redis_client
from src.modules.analytics.api.email_metrics import router as email_router
from src.modules.analytics.application.config import ETLConfig
from src.modules.analytics.application.dto.adoption_dto import AdoptionDetailDTO
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO
from src.modules.analytics.application.dto.capture_dto import CaptureDetailDTO
from src.modules.analytics.application.dto.channel_dashboard_dto import (
    ChannelDashboardDTO,
    DemographicsDTO,
)
from src.modules.analytics.application.dto.evangelization_dto import (
    EvangelizationDetailDTO,
)
from src.modules.analytics.application.dto.expansion_dto import ExpansionDetailDTO
from src.modules.analytics.application.dto.group_detail_dto import GroupDetailDTO
from src.modules.analytics.application.dto.nurture_dto import NurtureDetailDTO
from src.modules.analytics.application.dto.opportunity_dto import OpportunityDetailDTO
from src.modules.analytics.application.dto.sales_dto import SalesDetailDTO
from src.modules.analytics.application.dto.stage_overview_dto import StageOverviewDTO
from src.modules.analytics.application.dto.summary_dto import BowtiesSummaryDTO
from src.modules.analytics.application.dto.timeseries_dto import StageTimeSeriesDTO
from src.modules.analytics.application.services.metrics_service import MetricsService
from src.modules.analytics.application.services.stage_services import (
    AdoptionStageService,
    AttractionStageService,
    CaptureStageService,
    EvangelizationStageService,
    ExpansionStageService,
    NurtureStageService,
    OpportunityStageService,
    SalesStageService,
    StageOverviewService,
)
from src.modules.analytics.application.services.stage_services.group_detail import (
    GroupDetailService,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.connections.application.services.connection_port_impl import (
    ConnectionPortImpl,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.application.services.offer_read_port_impl import (
    OfferReadPortImpl,
)

router = APIRouter(prefix="/metrics", tags=["Marketing Metrics"])
router.include_router(email_router)

# Refresh cooldown: derived from centralized config
_REFRESH_COOLDOWN = timedelta(seconds=ETLConfig.PER_PROVIDER_REFRESH_COOLDOWN)


# ─── Sync All DTOs ────────────────────────────────────────────────────────────


class SyncProviderResult(BaseModel):
    provider: str
    status: str  # "ok" | "skipped_cooldown" | "failed"
    loaded: int | None = None
    skipped: int | None = None
    total: int | None = None
    remaining_minutes: int | None = None
    error: str | None = None


class SyncAllResponse(BaseModel):
    status: str
    providers_synced: int
    providers_skipped_cooldown: int
    providers_failed: int
    total_loaded: int
    total_skipped: int
    details: list[SyncProviderResult]


# ─── Sankey DTOs ──────────────────────────────────────────────────────────────


class SankeyNodeDTO(BaseModel):
    name: str


class SankeyLinkDTO(BaseModel):
    source: int
    target: int
    value: int


class SankeyRawMetricsDTO(BaseModel):
    visitors: int
    leads: int
    qualified: int
    opportunities: int
    customers: int
    retention: int
    evangelists: int


class MarketingSankeyResponse(BaseModel):
    nodes: list[SankeyNodeDTO]
    links: list[SankeyLinkDTO]
    raw_metrics: SankeyRawMetricsDTO


# ─── Channel Refresh DTO ──────────────────────────────────────────────────────


class ChannelRefreshResponse(BaseModel):
    status: str
    run_id: str
    provider: str
    channel_slug: str


# ─── Initial Load DTOs ────────────────────────────────────────────────────────


class InitialLoadResponse(BaseModel):
    status: str
    total_days: int
    loaded_days: int
    skipped_days: int


class InitialLoadStatusResponse(BaseModel):
    status: str
    total: int | None = None
    loaded: int | None = None
    skipped: int | None = None
    current_day: str | None = None


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
    "website-total": "google_analytics",
    "meta-pixel": "meta_pixel",
}


@router.get("/summary", response_model=BowtiesSummaryDTO)
async def get_summary_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lightweight KPIs for the Bowtie funnel row.

    Returns ~15 fields total (2 KPIs per stage × 8 stages) instead of
    the ~2000+ fields from 8 individual detail endpoints.
    Cache-first: reads from per-stage Redis caches with 60s summary TTL.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    offer_port = OfferReadPortImpl(db)
    service = MetricsService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    return await service.get_bowtie_summary(user.tenant_id)


@router.get("/sankey", response_model=MarketingSankeyResponse)
async def get_marketing_sankey(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Get Marketing Sankey Metrics (7 Nodes).
    """
    service = MetricsService(db)
    return service.get_marketing_sankey_metrics(user.tenant_id)


_VALID_PERIODS = {"last_30_days", "weekly", "monthly", "quarterly"}


# ─── Group Filter Helper ─────────────────────────────────────────────────────

# Group field names per stage DTO (fields that hold TrafficGroupDTO or similar)
_STAGE_GROUP_FIELDS: dict[str, list[str]] = {
    "attraction": ["organic_social", "ga4_search", "paid", "outbound", "website"],
    "capture": ["web_infrastructure", "ai_agent"],
    "nurturing": ["retargeting", "automation"],
    "opportunity": ["checkout", "payment_links", "qualification"],
    "sales": ["adquisicion", "expansion"],
    "expansion": ["retencion", "crecimiento", "cancelaciones"],
}

T = TypeVar("T", bound=BaseModel)


def _filter_groups(dto: T, requested_groups: list[str]) -> T:
    """Filter a stage detail DTO to include only requested groups.

    Excluded group fields are set to None (if Optional) or to an empty
    group dict (if required). Non-group fields (header_kpis, mini_funnel,
    period, etc.) are preserved.
    Returns a new DTO instance (immutable copy).
    """
    data = dto.model_dump()

    # Determine which fields are groups by checking all known stage group fields
    all_group_fields: set[str] = set()
    for fields in _STAGE_GROUP_FIELDS.values():
        all_group_fields.update(fields)

    # Check which fields are optional in the DTO schema
    optional_fields: set[str] = set()
    for name, field_info in dto.__class__.model_fields.items():
        if not field_info.is_required():
            optional_fields.add(name)

    empty_group = {"totals": {}, "channels": []}

    for field_name in all_group_fields:
        if field_name in data and field_name not in requested_groups:
            data[field_name] = None if field_name in optional_fields else empty_group

    return dto.__class__(**data)


# ─── Stage Overview Endpoint ─────────────────────────────────────────────────


async def _warm_stage_cache(
    db: Session,
    cache: MetricsCache,
    tenant_id,
    stage: str,
    period: str,
) -> None:
    """Call the stage service to populate the Redis cache for a stage.

    Called as a fallback when the overview endpoint finds an empty cache.
    The stage service queries the DB and caches the result, so a
    subsequent overview read will find data.
    """
    try:
        connection_port = ConnectionPortImpl(db)
        if stage == "attraction":
            svc = AttractionStageService(
                db, cache=cache, connection_port=connection_port
            )
            await svc.get_metrics(tenant_id, period=period)
        elif stage == "capture":
            svc = CaptureStageService(db, cache=cache, connection_port=connection_port)
            await svc.get_metrics(tenant_id, period=period)
        elif stage == "nurture":
            svc = NurtureStageService(db, cache=cache, connection_port=connection_port)
            await svc.get_metrics(tenant_id, period=period)
        elif stage == "opportunity":
            svc = OpportunityStageService(
                db, cache=cache, connection_port=connection_port
            )
            now = datetime.now(UTC)
            await svc.get_metrics(tenant_id, now - timedelta(days=30), now)
        elif stage in ("sales", "adoption", "expansion", "evangelization"):
            offer_port = OfferReadPortImpl(db)
            stage_cls = {
                "sales": SalesStageService,
                "adoption": AdoptionStageService,
                "expansion": ExpansionStageService,
                "evangelization": EvangelizationStageService,
            }[stage]
            svc = stage_cls(
                db, cache=cache, connection_port=connection_port, offer_port=offer_port
            )
            now = datetime.now(UTC)
            await svc.get_metrics(tenant_id, now - timedelta(days=30), now)
    except Exception:
        import structlog

        structlog.get_logger().warning(
            "stage_cache_warm_failed", stage=stage, tenant_id=str(tenant_id)
        )


class FunnelStage(str, Enum):
    """Valid funnel stages for the overview endpoint."""

    attraction = "attraction"
    capture = "capture"
    nurture = "nurture"
    opportunity = "opportunity"
    sales = "sales"
    adoption = "adoption"
    expansion = "expansion"
    evangelization = "evangelization"


@router.get("/{stage}/overview", response_model=StageOverviewDTO)
async def get_stage_overview(
    stage: FunnelStage = Path(...),
    period: str = Query(default="last_30_days"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lightweight overview for a funnel stage.

    Returns ~50-100 fields (header KPIs, channel list with 1 headline KPI,
    group summaries, optional mini-funnel and bottlenecks) instead of the
    ~500+ fields from the full detail endpoint.

    Cache-first with DB fallback: reads from Redis caches, but when cache
    is empty falls back to the detail service to query DB and warm cache.
    """
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    cache = MetricsCache(redis_client)
    overview_svc = StageOverviewService(cache=cache)
    overview = await overview_svc.get_stage_overview(
        str(user.tenant_id), stage.value, period
    )

    # Fallback: if cache was empty, warm it via the stage service (DB query)
    if not overview.channel_list and not overview.groups:
        await _warm_stage_cache(db, cache, user.tenant_id, stage.value, period)
        # Invalidate any stale overview cache before re-reading
        try:
            overview_key = cache._key(
                str(user.tenant_id), f"overview_{stage.value}", period
            )
            cache._redis.delete(overview_key)
        except Exception:
            import structlog

            structlog.get_logger().debug(
                "overview_cache_invalidation_failed", stage=stage.value
            )
        overview = await overview_svc.get_stage_overview(
            str(user.tenant_id), stage.value, period
        )

    return overview


@router.get("/{stage}/groups/{group_key}", response_model=GroupDetailDTO)
async def get_group_detail(
    stage: FunnelStage = Path(...),
    group_key: str = Path(...),
    period: str = Query(default="last_30_days"),
    user: User = Depends(get_current_user),
):
    """Detail for a single channel group within a stage (Tier 2).

    Returns full metrics for one group's channels only, much lighter
    than the full stage detail endpoint. Cache-first with 5-min TTL.
    """
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")

    cache = MetricsCache(redis_client)
    service = GroupDetailService(cache=cache)
    return await service.get_group_detail(
        str(user.tenant_id), stage.value, group_key, period
    )


@router.get("/attraction", response_model=AttractionDetailDTO)
async def get_attraction_metrics(
    period: str = Query(default="last_30_days"),
    groups: str | None = Query(
        default=None,
        description="Comma-separated group keys to filter (e.g., organic_social,paid)",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Attraction stage metrics with dynamic channel list from ETL tables.

    Supports period-aware queries: last_30_days, weekly, monthly, quarterly.
    Optional ?groups= filter returns only requested channel groups.
    """
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = AttractionStageService(db, cache=cache, connection_port=connection_port)
    result = await service.get_metrics(user.tenant_id, period=period)
    if groups:
        return _filter_groups(result, groups.split(","))
    return result


@router.get("/capture", response_model=CaptureDetailDTO)
async def get_capture_metrics(
    period: str = Query(default="last_30_days"),
    groups: str | None = Query(
        default=None,
        description="Comma-separated group keys to filter (e.g., web_infrastructure,ai_agent)",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Capture (Stage 1) detail panel metrics."""
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = CaptureStageService(db, cache=cache, connection_port=connection_port)
    result = await service.get_metrics(user.tenant_id, period=period)
    if groups:
        return _filter_groups(result, groups.split(","))
    return result


@router.get("/nurturing", response_model=NurtureDetailDTO)
async def get_nurturing_metrics(
    period: str = Query(default="last_30_days"),
    groups: str | None = Query(
        default=None,
        description="Comma-separated group keys to filter (e.g., retargeting,automation)",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get Nurturing (Stage 2) detail panel metrics."""
    if period not in _VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period: {period}")
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = NurtureStageService(db, cache=cache, connection_port=connection_port)
    result = await service.get_metrics(user.tenant_id, period=period)
    if groups:
        return _filter_groups(result, groups.split(","))
    return result


@router.get("/opportunity", response_model=OpportunityDetailDTO)
async def get_opportunity_metrics(
    groups: str | None = Query(
        default=None,
        description="Comma-separated group keys to filter (e.g., checkout,payment_links)",
    ),
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
    service = OpportunityStageService(db, cache=cache, connection_port=connection_port)
    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    result = await service.get_metrics(user.tenant_id, start_date, now)
    if groups:
        return _filter_groups(result, groups.split(","))
    return result


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
    service = SalesStageService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    return await service.get_metrics(user.tenant_id, start_date, now)


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
    service = AdoptionStageService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    return await service.get_metrics(user.tenant_id, start_date, now)


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
    service = ExpansionStageService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    return await service.get_metrics(user.tenant_id, start_date, now)


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
    service = EvangelizationStageService(
        db, cache=cache, connection_port=connection_port, offer_port=offer_port
    )
    now = datetime.now(UTC)
    start_date = now - timedelta(days=30)
    return await service.get_metrics(user.tenant_id, start_date, now)


_VALID_STAGES = {
    "attraction",
    "capture",
    "nurture",
    "opportunity",
    "sales",
    "adoption",
    "expansion",
    "evangelization",
}
_VALID_GRANULARITIES = {"daily", "weekly"}
_VALID_RANGES = {7, 30, 90}


@router.get("/timeseries", response_model=StageTimeSeriesDTO)
async def get_stage_timeseries(
    stage: str = Query(default="attraction"),
    metric: str = Query(default="visitors"),
    range_days: int = Query(default=30),
    granularity: str = Query(default="daily"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generic time-series endpoint for chart visualizations.

    Returns daily/weekly data points grouped by channel for any funnel stage.
    Reusable across all stages — just change the stage and metric params.
    """
    if stage not in _VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    if granularity not in _VALID_GRANULARITIES:
        raise HTTPException(
            status_code=400, detail=f"Invalid granularity: {granularity}"
        )
    if range_days not in _VALID_RANGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid range_days: {range_days}. Use 7, 30, or 90.",
        )

    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    return await service.get_stage_timeseries(
        user.tenant_id, stage, metric, range_days, granularity
    )


_SYNC_ALL_COOLDOWN = timedelta(minutes=2)


@router.post("/sync", response_model=SyncAllResponse)
async def sync_all_sources(
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync all connected providers for the tenant.

    Runs gap-detection initial-load for each provider with an active
    connection. Fast when data is up to date (short-circuit, no API calls).
    Global 2-min cooldown prevents concurrent or back-to-back syncs.
    Per-provider 15-min cooldown — skipped providers report remaining time.
    """
    from src.modules.analytics.application.services.etl_service import ETLService

    # Global cooldown: prevent back-to-back or concurrent syncs for the same tenant.
    cooldown_key = f"sync_all:{user.tenant_id}"
    if redis_client:
        last_sync = redis_client.get(cooldown_key)
        if last_sync:
            elapsed = datetime.now(UTC) - datetime.fromisoformat(last_sync)
            remaining = _SYNC_ALL_COOLDOWN - elapsed
            if remaining.total_seconds() > 0:
                raise HTTPException(
                    status_code=429,
                    detail=f"Sync en progreso o muy reciente. Espera {int(remaining.total_seconds())}s antes de volver a sincronizar.",
                )
        redis_client.setex(
            cooldown_key,
            int(_SYNC_ALL_COOLDOWN.total_seconds()),
            datetime.now(UTC).isoformat(),
        )

    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    etl = ETLService(db, connection_port=connection_port, cache=cache)

    result = await etl.run_sync_all(user.tenant_id, days=days)
    return SyncAllResponse(**result)


class MetricCatalogEntryResponse(BaseModel):
    """Single metric entry in the catalog response."""

    name: str
    display_name: str
    description: str
    interpretation: str
    unit: str
    aggregation: str
    is_unique_metric: bool
    higher_is_better: bool
    providers: list[str]
    weight_metric: str | None = None
    formula: str | None = None
    formula_components: list[str] = []
    benchmarks: str | None = None


class MetricCatalogResponse(BaseModel):
    """Full metric catalog response."""

    metrics: list[MetricCatalogEntryResponse]
    count: int


class SyncIgDmResponse(BaseModel):
    status: str
    synced_messages: int
    new_leads: int
    skipped: int
    remaining_minutes: int | None = None


@router.post("/sync-ig-dm", response_model=SyncIgDmResponse)
async def sync_ig_dm(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sync Instagram DM conversations via the Conversations API.

    Fetches historical DM messages and creates journey_events with dedup
    by message_id. Applies a 15-min cooldown to prevent abuse.
    """
    # Cooldown check using Redis
    cooldown_key = f"ig_dm_sync:{user.tenant_id}"
    if redis_client:
        last_sync = redis_client.get(cooldown_key)
        if last_sync:
            import json

            elapsed_info = json.loads(last_sync)
            from datetime import datetime as dt

            last_ts = dt.fromisoformat(elapsed_info["ts"])
            elapsed = datetime.now(UTC) - last_ts
            if elapsed < _REFRESH_COOLDOWN:
                remaining = _REFRESH_COOLDOWN - elapsed
                remaining_min = int(remaining.total_seconds() // 60) + 1
                return SyncIgDmResponse(
                    status="cooldown",
                    synced_messages=0,
                    new_leads=0,
                    skipped=0,
                    remaining_minutes=remaining_min,
                )

    from src.modules.analytics.application.services.ig_dm_sync_service import (
        InstagramDMSyncService,
    )

    connection_port = ConnectionPortImpl(db)
    sync_service = InstagramDMSyncService(db, connection_port=connection_port)

    try:
        result = await sync_service.sync(user.tenant_id)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"IG DM sync failed: {exc!s}",
        )

    # Set cooldown
    if redis_client:
        import json

        redis_client.setex(
            cooldown_key,
            int(_REFRESH_COOLDOWN.total_seconds()),
            json.dumps({"ts": datetime.now(UTC).isoformat()}),
        )

    return SyncIgDmResponse(
        status="ok",
        synced_messages=result["synced_messages"],
        new_leads=result["new_leads"],
        skipped=result["skipped"],
    )


@router.post(
    "/attraction/refresh/{channel_slug}", response_model=ChannelRefreshResponse
)
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
        elapsed = datetime.now(UTC) - latest_run.started_at
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
        return ChannelRefreshResponse(
            status="ok",
            run_id=str(run.id),
            provider=provider_name,
            channel_slug=channel_slug,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {exc!s}",
        )


@router.get("/catalog", response_model=MetricCatalogResponse)
def get_metric_catalog(
    user: User = Depends(get_current_user),
) -> MetricCatalogResponse:
    """Return the full metric catalog with aggregation semantics.

    Useful for frontend to display metric descriptions, units, and
    understand which metrics should NOT be summed across time periods.
    """
    from src.modules.analytics.domain.metric_catalog import METRIC_CATALOG

    entries = [
        MetricCatalogEntryResponse(
            name=defn.name,
            display_name=defn.display_name,
            description=defn.description,
            interpretation=defn.interpretation,
            unit=defn.unit.value,
            aggregation=defn.aggregation.value,
            is_unique_metric=defn.is_unique_metric,
            higher_is_better=defn.higher_is_better,
            providers=list(defn.providers),
            weight_metric=defn.weight_metric,
            formula=defn.formula,
            formula_components=list(defn.formula_components),
            benchmarks=defn.benchmarks,
        )
        for defn in METRIC_CATALOG.values()
    ]
    return MetricCatalogResponse(metrics=entries, count=len(entries))


@router.get(
    "/channel/{channel_slug}/dashboard",
    response_model=ChannelDashboardDTO,
)
async def get_channel_dashboard(
    channel_slug: str,
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a channel-specific dashboard with KPIs, benchmarks, time series, and funnel.

    Returns industry-contextualized benchmarks based on the tenant's brand identity.
    Generic endpoint — works for any channel slug, not just meta-ads.
    """
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Use 7d, 30d, or 90d.",
        )

    from src.modules.analytics.application.services.channel_dashboard_service import (
        ChannelDashboardService,
    )
    from src.modules.brand.application.services.brand_read_port_impl import (
        BrandReadPortImpl,
    )

    brand_port = BrandReadPortImpl(db)
    service = ChannelDashboardService(db, brand_port=brand_port)
    return await service.get_dashboard(user.tenant_id, channel_slug, period)


@router.get(
    "/channel/{channel_slug}/demographics",
    response_model=DemographicsDTO,
)
async def get_channel_demographics(
    channel_slug: str,
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get audience demographics breakdown for a channel.

    Parses breakdown data from official_metrics extra JSON column for
    age, gender, and placement segmentation. Returns percentage distribution.
    """
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Use 7d, 30d, or 90d.",
        )

    from src.modules.analytics.application.services.channel_dashboard_service import (
        ChannelDashboardService,
    )

    service = ChannelDashboardService(db)
    return service.get_demographics(user.tenant_id, channel_slug, period)


_VALID_PROVIDERS = {"meta", "google_analytics", "google_ads", "shopify", "mailerlite"}


@router.post("/{provider}/initial-load", response_model=InitialLoadResponse)
async def trigger_initial_load(
    provider: str,
    days: int = Query(default=30, ge=1, le=ETLConfig.MAX_LOOKBACK_DAYS),
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
        elapsed = datetime.now(UTC) - latest_run.started_at
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
        return InitialLoadResponse(
            status="ok",
            total_days=result["total"],
            loaded_days=result["loaded"],
            skipped_days=result["skipped"],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Initial load failed: {exc!s}",
        )


@router.get("/{provider}/initial-load/status", response_model=InitialLoadStatusResponse)
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
        return InitialLoadStatusResponse(status="idle")

    try:
        data = json.loads(raw)
        return InitialLoadStatusResponse(**data)
    except (json.JSONDecodeError, TypeError, ValueError):
        return InitialLoadStatusResponse(status="idle")


# ─── Period Extraction Endpoints ─────────────────────────────────────────────


class PeriodExtractionRequest(BaseModel):
    period_type: str  # weekly, monthly, quarterly
    period_start: date
    period_end: date


class PeriodExtractionResultDTO(BaseModel):
    provider: str
    status: str
    metrics_count: int | None = None
    period_type: str | None = None
    reason: str | None = None
    error: str | None = None


class PeriodExtractionResponse(BaseModel):
    status: str
    results: list[PeriodExtractionResultDTO]


@router.post("/trigger-period-extraction", response_model=PeriodExtractionResponse)
async def trigger_period_extraction(
    period_type: str = Query(...),
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Manually trigger period extraction for NON_AGGREGABLE metrics.

    Extracts deduplicated reach/users/frequency for all providers
    that support period-level extraction.
    """
    if period_type not in {"weekly", "monthly", "quarterly"}:
        raise HTTPException(
            status_code=400, detail=f"Invalid period_type: {period_type}"
        )

    if period_end < period_start:
        raise HTTPException(
            status_code=400, detail="period_end must be >= period_start"
        )

    from src.modules.analytics.application.services.etl_service import ETLService

    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    etl = ETLService(db, connection_port=connection_port, cache=cache)

    try:
        results = await etl.run_period_extraction(
            tenant_id=user.tenant_id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
        )
        return PeriodExtractionResponse(
            status="ok",
            results=[PeriodExtractionResultDTO(**r) for r in results],
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Period extraction failed: {exc!s}",
        )


# ─── Tenant Period Config Endpoint ───────────────────────────────────────────


class TenantPeriodConfigDTO(BaseModel):
    weekly_start_day: int
    fiscal_year_start_month: int
    fiscal_year_start_day: int


class TenantPeriodConfigUpdateDTO(BaseModel):
    weekly_start_day: int | None = None
    fiscal_year_start_month: int | None = None
    fiscal_year_start_day: int | None = None


@router.get("/period-config", response_model=TenantPeriodConfigDTO)
async def get_period_config(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get the tenant's period configuration."""
    from sqlalchemy import select as sa_select

    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    tenant = db.execute(
        sa_select(TenantModel).where(TenantModel.id == user.tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return TenantPeriodConfigDTO(
        weekly_start_day=tenant.weekly_start_day or 0,
        fiscal_year_start_month=tenant.fiscal_year_start_month or 1,
        fiscal_year_start_day=tenant.fiscal_year_start_day or 1,
    )


@router.patch("/period-config", response_model=TenantPeriodConfigDTO)
async def update_period_config(
    payload: TenantPeriodConfigUpdateDTO,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update the tenant's period configuration.

    Changes affect future aggregation calculations and period boundary detection.
    """
    from sqlalchemy import select as sa_select
    from sqlalchemy import update as sa_update

    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    tenant = db.execute(
        sa_select(TenantModel).where(TenantModel.id == user.tenant_id)
    ).scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    updates = {}
    if payload.weekly_start_day is not None:
        if not 0 <= payload.weekly_start_day <= 6:
            raise HTTPException(status_code=400, detail="weekly_start_day must be 0-6")
        updates["weekly_start_day"] = payload.weekly_start_day
    if payload.fiscal_year_start_month is not None:
        if not 1 <= payload.fiscal_year_start_month <= 12:
            raise HTTPException(
                status_code=400, detail="fiscal_year_start_month must be 1-12"
            )
        updates["fiscal_year_start_month"] = payload.fiscal_year_start_month
    if payload.fiscal_year_start_day is not None:
        if not 1 <= payload.fiscal_year_start_day <= 31:
            raise HTTPException(
                status_code=400, detail="fiscal_year_start_day must be 1-31"
            )
        updates["fiscal_year_start_day"] = payload.fiscal_year_start_day

    if updates:
        db.execute(
            sa_update(TenantModel)
            .where(TenantModel.id == user.tenant_id)
            .values(**updates)
        )
        db.commit()

        # Invalidate cache so new config is picked up
        cache = MetricsCache(redis_client)
        await cache.invalidate_tenant(str(user.tenant_id))

    # Reload
    db.expire_all()
    tenant = db.execute(
        sa_select(TenantModel).where(TenantModel.id == user.tenant_id)
    ).scalar_one()

    return TenantPeriodConfigDTO(
        weekly_start_day=tenant.weekly_start_day or 0,
        fiscal_year_start_month=tenant.fiscal_year_start_month or 1,
        fiscal_year_start_day=tenant.fiscal_year_start_day or 1,
    )
