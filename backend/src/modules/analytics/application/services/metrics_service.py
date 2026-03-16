"""MetricsService -- dashboard data for marketing funnel visualization.

get_attraction_metrics() reads from ETL official tables via:
- MetricsCache (5-min Redis TTL)
- OfficialMetricsRepository / MetricAggregationModel
- ChannelRegistry (dynamic channel list from ConnectionPort)

get_marketing_sankey_metrics() still reads from journey_events (separate migration).
"""

from collections import defaultdict
from uuid import UUID
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.repositories.customer_repository import (
    JourneyEventRepository,
    CustomerRepository,
)
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
    LeadRepository,
)
from src.modules.crm.domain.enums import LifecycleStage
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    TrafficGroupDTO,
    ChannelMetricDTO,
    MetricValueDTO,
)
from src.modules.analytics.application.dto.capture_dto import (
    CaptureDetailDTO,
    CaptureHeaderKpisDTO,
    MiniFunnelDTO,
)
from src.modules.analytics.application.dto.nurture_dto import (
    NurtureDetailDTO,
    NurtureHeaderKpisDTO,
)
from src.modules.analytics.application.dto.opportunity_dto import (
    OpportunityDetailDTO,
    OpportunityHeaderKpisDTO,
    BottleneckDTO,
)
from src.modules.analytics.application.dto.sales_dto import (
    SalesDetailDTO,
    SalesHeaderKpisDTO,
    RevenueGroupDTO,
    TierGroupDTO,
    OfferSaleDTO,
    get_tier_for_value_level,
    get_subscription_labels,
    convert_to_usd,
    TIER_DISPLAY_ORDER,
    TIER_LABELS,
    LOW_CONVERSION_THRESHOLDS,
    HIGH_CAC_WARNING_RATIO,
    HIGH_CAC_CRITICAL_RATIO,
)
from src.modules.analytics.infrastructure.repositories.nurture_repository import (
    NurtureMetricsRepository,
)
from src.modules.analytics.application.services.stage_cost_service import (
    StageCostService,
)
from src.modules.analytics.infrastructure.repositories.capture_repository import (
    CaptureMetricsRepository,
)
from src.modules.analytics.application.services.capture_cost_service import (
    CaptureCostService,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.application.services.channel_registry import (
    ChannelRegistry,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort

# Maps our channel slugs to the ChannelType enum for connection lookups (sankey legacy)
_CHANNEL_CONNECTION_MAP: Dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,
    "yt-ads": ChannelType.YOUTUBE,
}

# Channel types -> group mapping for the 4-group structure
_GROUP_MAP: Dict[str, str] = {
    "social": "organic_social",
    "search": "ga4_search",
    "direct": "ga4_search",
    "paid": "paid",
    "outbound": "outbound",
}

# Channel types -> capture group mapping (Stage 1)
_CAPTURE_GROUP_MAP: Dict[str, str] = {
    "form": "web_infrastructure",
    "email": "web_infrastructure",
    "messaging": "ai_agent",
}

# Channel types -> nurture group mapping (Stage 2)
_NURTURE_GROUP_MAP: Dict[str, str] = {
    "retargeting": "retargeting",
    "email": "automation",
    "automation": "automation",
}

# Channel types -> opportunity group mapping (Stage 3)
_OPPORTUNITY_GROUP_MAP: Dict[str, str] = {
    "checkout": "checkout",
    "payment_link": "payment_links",
    "qualification": "qualification",
}

# Error message mapping from extraction run errors to user-facing messages
_ERROR_MESSAGES: Dict[str, str] = {
    "token_expired": "Token expirado",
    "token_refresh_failed": "Token expirado",
    "connection_revoked": "Token expirado",
    "rate_limited": "Reintentando...",
    "rate_limit": "Reintentando...",
    "provider_error": "Servicio no disponible",
    "timeout": "Servicio no disponible",
    "http_5xx": "Servicio no disponible",
}


class MetricsService:
    """Provides dashboard metrics for marketing funnel stages.

    Constructor accepts optional cache and connection_port for backward
    compatibility -- the sankey endpoint doesn't need them.
    """

    def __init__(
        self,
        db: Session,
        cache: Optional[MetricsCache] = None,
        connection_port: Optional[ConnectionPort] = None,
        offer_port: Optional[OfferReadPort] = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port
        self.offer_port = offer_port

        # Legacy repos for sankey (unchanged)
        self.journey_repo = JourneyEventRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)
        self.connection_repo = ChannelConnectionRepository(db)

    def get_marketing_sankey_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Obtiene metricas para el diagrama de Sankey de marketing (7 nodos).

        Nodos:
        0: Adquisition (Visitors)
        1: Activation (Leads)
        2: Consideration (Qualified Leads)
        3: Decision (Opportunities)
        4: Conversion (Customers)
        5: Retention (Loyal Customers)
        6: Advocacy (Evangelists)
        """

        # 1. Visitors (Adquisition)
        visitors = self.journey_repo.get_unique_visitors(tenant_id)

        # 2. Leads (Activation)
        leads = self.lead_repo.count_total(tenant_id)

        # 3. Qualified (Consideration)
        qualified_leads = self.lead_repo.count_qualified(tenant_id)
        mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
        qualified = max(qualified_leads, mql_count)

        # 4. Opportunities (Decision)
        sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
        opp_count = self.customer_repo.count_by_stage(
            tenant_id, LifecycleStage.OPPORTUNITY
        )
        opportunities = sql_count + opp_count

        # 5. Customers (Conversion)
        customers = self.customer_repo.count_by_stage(
            tenant_id, LifecycleStage.CUSTOMER
        )

        # 6. Loyal Customers (Retention)
        # Placeholder heuristic: 40% of customers are retained/loyal
        retention = int(customers * 0.4)

        # 7. Evangelists (Advocacy)
        evangelists = self.customer_repo.count_by_stage(
            tenant_id, LifecycleStage.EVANGELIST
        )

        nodes = [
            {"name": "Adquisition"},
            {"name": "Activation"},
            {"name": "Consideration"},
            {"name": "Decision"},
            {"name": "Conversion"},
            {"name": "Retention"},
            {"name": "Advocacy"},
        ]

        links = [
            {"source": 0, "target": 1, "value": leads},
            {"source": 1, "target": 2, "value": qualified},
            {"source": 2, "target": 3, "value": opportunities},
            {"source": 3, "target": 4, "value": customers},
            {"source": 4, "target": 5, "value": retention},
            {"source": 5, "target": 6, "value": evangelists},
        ]

        return {
            "nodes": nodes,
            "links": links,
            "raw_metrics": {
                "visitors": visitors,
                "leads": leads,
                "qualified": qualified,
                "opportunities": opportunities,
                "customers": customers,
                "retention": retention,
                "evangelists": evangelists,
            },
        }

    def _is_connected(self, tenant_id: UUID, slug: str) -> bool:
        """Check if a channel has an active connection for this tenant."""
        channel_type = _CHANNEL_CONNECTION_MAP.get(slug)
        if not channel_type:
            return False
        conn = self.connection_repo.get_active(tenant_id, channel_type)
        return conn is not None

    def _classify_error(self, error_text: Optional[str]) -> Optional[str]:
        """Map extraction error to a user-facing message."""
        if not error_text:
            return None
        error_lower = error_text.lower()
        for key, msg in _ERROR_MESSAGES.items():
            if key in error_lower:
                return msg
        return "Servicio no disponible"

    async def get_attraction_metrics(
        self, tenant_id: UUID
    ) -> AttractionDetailDTO:
        """Return attraction-stage metrics from ETL official tables.

        Flow:
        1. Check MetricsCache (5-min TTL)
        2. On miss: ChannelRegistry -> OfficialMetricsRepository -> build DTOs
        3. Build multi-metric ChannelMetricDTO objects per channel
        4. Group into 4 sections: organic_social, ga4_search, paid, outbound
        5. Cache result before returning
        """
        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "attraction", "last_30_days"
            )
            if cached is not None:
                return AttractionDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(
            tenant_id, "attraction"
        )

        # 3. Get aggregated metrics from official tables
        repo = OfficialMetricsRepository(self.db)
        aggregations = repo.get_channel_summary(
            tenant_id, "attraction", "last_30_days"
        )

        # Build lookup: channel_slug -> list of aggregation rows (multi-metric)
        agg_by_slug: Dict[str, List[Any]] = defaultdict(list)
        for agg in aggregations:
            agg_by_slug[agg.channel_slug].append(agg)

        # 4. Get extraction run status for stale detection
        from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
            ExtractionRunRepository,
        )
        run_repo = ExtractionRunRepository(self.db)

        # Build provider -> latest run lookup (deduplicate per provider)
        provider_runs: Dict[str, Any] = {}

        # 5. Build ChannelMetricDTO lists grouped by section
        groups: Dict[str, List[ChannelMetricDTO]] = {
            "organic_social": [],
            "ga4_search": [],
            "paid": [],
            "outbound": [],
        }
        available_channels: List[ChannelMetricDTO] = []
        latest_updated: Optional[str] = None

        # Connected channels
        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            channel_type = ch["channel_type"]
            group_key = _GROUP_MAP.get(channel_type, "organic_social")

            # Build MetricValueDTO list from aggregation rows
            agg_rows = agg_by_slug.get(slug, [])
            metrics: List[MetricValueDTO] = []
            last_updated: Optional[str] = None

            for agg in agg_rows:
                extra_data = getattr(agg, "extra", None) or {}
                breakdown = extra_data if isinstance(extra_data, dict) and extra_data else None

                metrics.append(MetricValueDTO(
                    name=agg.metric_name,
                    value=agg.value,
                    unit=agg.unit or "count",
                    currency=getattr(agg, "currency", None),
                    breakdown=breakdown,
                ))

                # Track latest computed_at for this channel
                if hasattr(agg, "computed_at") and agg.computed_at:
                    ts = agg.computed_at.isoformat()
                    if last_updated is None or ts > last_updated:
                        last_updated = ts
                    if latest_updated is None or ts > latest_updated:
                        latest_updated = ts

            # Stale detection: check extraction run for provider
            provider_name = ch.get("provider_name", "")
            stale = False
            error_message = None

            if provider_name and provider_name not in ("internal", "manual"):
                if provider_name not in provider_runs:
                    provider_runs[provider_name] = run_repo.get_latest(
                        tenant_id, provider_name
                    )
                latest_run = provider_runs[provider_name]
                if latest_run:
                    if latest_run.status in ("failed", "retrying"):
                        stale = True
                        error_message = self._classify_error(latest_run.error)

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
                cost_type=getattr(agg_rows[0], "cost_type", None) if agg_rows else None,
                last_updated=last_updated,
                stale=stale,
                error_message=error_message,
            )

            groups[group_key].append(dto)

        # Available (unconnected) channels
        for ch in channel_split.get("available", []):
            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                metrics=[],
                source_label=ch["source_label"],
                connected=False,
            )
            available_channels.append(dto)

        # 6. Compute group totals
        def _compute_totals(channels: List[ChannelMetricDTO]) -> Dict[str, float]:
            totals: Dict[str, float] = defaultdict(float)
            for ch in channels:
                for m in ch.metrics:
                    totals[m.name] += m.value
            return dict(totals)

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        result = AttractionDetailDTO(
            organic_social=TrafficGroupDTO(
                totals=_compute_totals(groups["organic_social"]),
                channels=groups["organic_social"],
            ),
            ga4_search=TrafficGroupDTO(
                totals=_compute_totals(groups["ga4_search"]),
                channels=groups["ga4_search"],
            ),
            paid=TrafficGroupDTO(
                totals=_compute_totals(groups["paid"]),
                channels=groups["paid"],
            ),
            outbound=TrafficGroupDTO(
                totals=_compute_totals(groups["outbound"]),
                channels=groups["outbound"],
            ),
            available=available_dto,
            period="last_30_days",
            last_updated=latest_updated,
        )

        # 7. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "attraction",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_capture_metrics(
        self, tenant_id: UUID
    ) -> CaptureDetailDTO:
        """Return capture-stage (Stage 1) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for capture stage)
        2. On miss: query CaptureMetricsRepository for lead counts by lead_source
        3. Query CaptureCostService for per-channel costs
        4. Get Stage 0 visitor total from MetricAggregationModel
        5. Map channels from STAGE_CHANNEL_MAP["capture"] via ChannelRegistry
        6. Group into web_infrastructure and ai_agent
        7. Calculate header KPIs and mini funnel
        8. Cache result and return CaptureDetailDTO
        """
        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "capture", "last_30_days"
            )
            if cached is not None:
                return CaptureDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(
            tenant_id, "capture"
        )

        # 3. Query CRM for lead counts by lead_source
        from datetime import datetime, timedelta, timezone as tz

        now = datetime.now(tz.utc)
        start_date = now - timedelta(days=30)
        end_date = now

        capture_repo = CaptureMetricsRepository(self.db)
        lead_counts = capture_repo.count_leads_by_source(
            tenant_id, start_date, end_date
        )
        conversation_counts = capture_repo.count_conversations_by_channel(
            tenant_id, start_date, end_date
        )

        # 4. Get costs
        cost_service = CaptureCostService(self.db)
        channel_costs = cost_service.get_channel_costs(tenant_id)

        # Get prorated agency costs
        connected_slugs = [ch["slug"] for ch in channel_split.get("connected", [])]
        prorated_costs = cost_service.get_prorated_agency_costs(
            tenant_id, connected_slugs
        )

        # Merge costs
        all_costs: Dict[str, float] = {}
        for slug, amount in channel_costs.items():
            all_costs[slug] = all_costs.get(slug, 0.0) + amount
        for slug, amount in prorated_costs.items():
            all_costs[slug] = all_costs.get(slug, 0.0) + amount

        # 5. Get Stage 0 visitor total from aggregations
        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )
        from sqlalchemy import select, func as sa_func

        visitor_stmt = (
            select(sa_func.coalesce(sa_func.sum(MetricAggregationModel.value), 0.0))
            .where(
                MetricAggregationModel.tenant_id == tenant_id,
                MetricAggregationModel.metric_name.in_(("reach", "sessions")),
                MetricAggregationModel.period_type == "last_30_days",
            )
        )
        stage0_visitors = int(self.db.execute(visitor_stmt).scalar() or 0)

        # 6. Build ChannelMetricDTO lists grouped by section
        groups: Dict[str, List[ChannelMetricDTO]] = {
            "web_infrastructure": [],
            "ai_agent": [],
        }
        available_channels: List[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            channel_type = ch["channel_type"]
            group_key = _CAPTURE_GROUP_MAP.get(channel_type, "web_infrastructure")

            lead_count = lead_counts.get(slug, 0)
            channel_cost = all_costs.get(slug, 0.0)
            conv_count = conversation_counts.get(slug, 0)

            # Conversion rate: leads / stage0_visitors * 100
            conv_rate = round(lead_count / stage0_visitors * 100, 2) if stage0_visitors > 0 else 0.0

            metrics: List[MetricValueDTO] = [
                MetricValueDTO(name="leads", value=float(lead_count)),
                MetricValueDTO(
                    name="cost",
                    value=channel_cost,
                    unit="currency",
                    currency="USD",
                ),
                MetricValueDTO(
                    name="conversion_rate",
                    value=conv_rate,
                    unit="percentage",
                ),
            ]

            # AI Agent channels: add conversation volume
            if channel_type == "messaging":
                metrics.append(
                    MetricValueDTO(name="conversations", value=float(conv_count))
                )

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
                cost_type="EXPENSE",
            )
            groups[group_key].append(dto)

        # Available (unconnected) channels
        for ch in channel_split.get("available", []):
            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                metrics=[],
                source_label=ch["source_label"],
                connected=False,
            )
            available_channels.append(dto)

        # 7. Compute group totals
        def _compute_totals(channels: List[ChannelMetricDTO]) -> Dict[str, float]:
            totals: Dict[str, float] = defaultdict(float)
            for ch_dto in channels:
                for m in ch_dto.metrics:
                    totals[m.name] += m.value
            return dict(totals)

        total_leads = sum(lead_counts.values())
        total_costs = sum(all_costs.values())
        overall_conv_rate = round(total_leads / stage0_visitors * 100, 2) if stage0_visitors > 0 else 0.0
        cal = cost_service.calculate_cal(total_costs, total_leads)

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        result = CaptureDetailDTO(
            header_kpis=CaptureHeaderKpisDTO(
                total_leads=total_leads,
                conversion_rate=overall_conv_rate,
                cost_per_lead=cal,
            ),
            mini_funnel=MiniFunnelDTO(
                source_label="Visitantes",
                source_value=stage0_visitors,
                target_label="Leads",
                target_value=total_leads,
                conversion_rate=overall_conv_rate,
            ),
            web_infrastructure=TrafficGroupDTO(
                totals=_compute_totals(groups["web_infrastructure"]),
                channels=groups["web_infrastructure"],
            ),
            ai_agent=TrafficGroupDTO(
                totals=_compute_totals(groups["ai_agent"]),
                channels=groups["ai_agent"],
            ),
            available=available_dto,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "capture",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_nurturing_metrics(
        self, tenant_id: UUID
    ) -> NurtureDetailDTO:
        """Return nurture-stage (Stage 2) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for nurture stage)
        2. On miss: query NurtureMetricsRepository for MQL counts
        3. Query StageCostService for costs with per-group breakdown
        4. Map channels from STAGE_CHANNEL_MAP["nurture"] via ChannelRegistry
        5. Group into retargeting and automation
        6. Build header KPIs and mini funnel (Leads -> MQLs)
        7. Cache result and return NurtureDetailDTO
        """
        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "nurture", "last_30_days"
            )
            if cached is not None:
                return NurtureDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(
            tenant_id, "nurture"
        )

        # 3. Get aggregated metrics from official tables
        repo = OfficialMetricsRepository(self.db)
        aggregations = repo.get_channel_summary(
            tenant_id, "nurture", "last_30_days"
        )

        # Build lookup: channel_slug -> list of aggregation rows
        agg_by_slug: Dict[str, List[Any]] = defaultdict(list)
        for agg in aggregations:
            agg_by_slug[agg.channel_slug].append(agg)

        # 4. Query CRM for MQL counts
        from datetime import datetime, timedelta, timezone as tz

        now = datetime.now(tz.utc)
        start_date = now - timedelta(days=30)

        nurture_repo = NurtureMetricsRepository(self.db)
        total_mqls = nurture_repo.count_new_mqls(tenant_id, start_date, now)
        total_leads = nurture_repo.count_leads_in_period(tenant_id, start_date, now)

        # 5. Query StageCostService for costs including per-group breakdown
        cost_svc = StageCostService(self.db)
        manual_costs = cost_svc.get_channel_costs(tenant_id, "nurture")
        retargeting_spend = cost_svc.get_retargeting_spend(tenant_id, start_date, now)
        all_costs = {**manual_costs, **retargeting_spend}
        total_cost = sum(all_costs.values())
        cost_per_mql = cost_svc.calculate_cost_per_mql(total_cost, total_mqls)

        # Per-group cost/MQL for group header display (locked CONTEXT.md decision)
        retargeting_cost_per_mql = cost_svc.get_group_cost_per_mql(
            "retargeting", tenant_id, start_date, now, total_mqls
        )
        automation_cost_per_mql = cost_svc.get_group_cost_per_mql(
            "automation", tenant_id, start_date, now, total_mqls
        )

        # 6. Query CRM for internal channel-specific data
        email_events = nurture_repo.count_email_events(tenant_id, start_date, now)
        followup_events = nurture_repo.count_followup_events(tenant_id, start_date, now)

        # 7. Build ChannelMetricDTO lists grouped by section
        groups: Dict[str, List[ChannelMetricDTO]] = {
            "retargeting": [],
            "automation": [],
        }
        available_channels: List[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            channel_type = ch["channel_type"]
            group_key = _NURTURE_GROUP_MAP.get(channel_type, "automation")

            # Build metrics depending on channel type
            metrics: List[MetricValueDTO] = []

            if slug == "mailerlite":
                # Mailerlite: email engagement metrics from CRM events
                emails_sent = email_events.get("emails_sent", 0)
                opens = email_events.get("opens", 0)
                clicks = email_events.get("clicks", 0)
                open_rate = round(opens / emails_sent * 100, 2) if emails_sent > 0 else 0.0
                click_rate = round(clicks / emails_sent * 100, 2) if emails_sent > 0 else 0.0

                metrics = [
                    MetricValueDTO(name="emails_sent", value=float(emails_sent)),
                    MetricValueDTO(name="open_rate", value=open_rate, unit="percentage"),
                    MetricValueDTO(name="click_rate", value=click_rate, unit="percentage"),
                ]
            elif slug == "ai-sdr":
                # AI SDR: followup metrics from CRM events
                sent = followup_events.get("sent", 0)
                replied = followup_events.get("replied", 0)
                response_rate = round(replied / sent * 100, 2) if sent > 0 else 0.0

                metrics = [
                    MetricValueDTO(name="followups", value=float(sent)),
                    MetricValueDTO(name="response_rate", value=response_rate, unit="percentage"),
                ]
            else:
                # Retargeting channels: metrics from ETL aggregation tables
                agg_rows = agg_by_slug.get(slug, [])
                for agg in agg_rows:
                    extra_data = getattr(agg, "extra", None) or {}
                    breakdown = extra_data if isinstance(extra_data, dict) and extra_data else None
                    metrics.append(MetricValueDTO(
                        name=agg.metric_name,
                        value=agg.value,
                        unit=agg.unit or "count",
                        currency=getattr(agg, "currency", None),
                        breakdown=breakdown,
                    ))

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
            )
            groups[group_key].append(dto)

        # Available (unconnected) channels
        for ch in channel_split.get("available", []):
            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                metrics=[],
                source_label=ch["source_label"],
                connected=False,
            )
            available_channels.append(dto)

        # 8. Compute group totals with per-group cost_per_mql
        def _compute_totals(channels: List[ChannelMetricDTO]) -> Dict[str, float]:
            totals: Dict[str, float] = defaultdict(float)
            for ch_dto in channels:
                for m in ch_dto.metrics:
                    totals[m.name] += m.value
            return dict(totals)

        retargeting_totals = _compute_totals(groups["retargeting"])
        if retargeting_cost_per_mql is not None:
            retargeting_totals["cost_per_mql"] = retargeting_cost_per_mql

        automation_totals = _compute_totals(groups["automation"])
        if automation_cost_per_mql is not None:
            automation_totals["cost_per_mql"] = automation_cost_per_mql

        # 9. Build header KPIs and mini funnel
        conversion_rate = round(total_mqls / total_leads * 100, 2) if total_leads > 0 else 0.0

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        result = NurtureDetailDTO(
            header_kpis=NurtureHeaderKpisDTO(
                total_mqls=total_mqls,
                conversion_rate=conversion_rate,
                cost_per_mql=cost_per_mql,
            ),
            mini_funnel=MiniFunnelDTO(
                source_label="Leads",
                source_value=total_leads,
                target_label="MQLs",
                target_value=total_mqls,
                conversion_rate=conversion_rate,
            ),
            retargeting=TrafficGroupDTO(
                totals=retargeting_totals,
                channels=groups["retargeting"],
            ),
            automation=TrafficGroupDTO(
                totals=automation_totals,
                channels=groups["automation"],
            ),
            available=available_dto,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 10. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "nurture",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_opportunity_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> OpportunityDetailDTO:
        """Return opportunity-stage (Stage 3) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for opportunity stage)
        2. On miss: query OpportunityMetricsRepository for SQL counts,
           checkout events, meeting events, payment link events
        3. Build channel groups: checkout, payment_links, qualification
        4. Calculate bottleneck flags (abandoned cart rate, no-show rate)
        5. Build header KPIs and mini funnel (MQLs -> SQLs)
        6. Cache result and return OpportunityDetailDTO
        """
        from datetime import datetime as dt_cls, timedelta, timezone as tz

        from src.modules.analytics.infrastructure.repositories.opportunity_repository import (
            OpportunityMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "opportunity", "last_30_days"
            )
            if cached is not None:
                return OpportunityDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(
            tenant_id, "opportunity"
        )

        # 3. Query CRM for SQL pipeline metrics
        repo = OpportunityMetricsRepository(self.db)
        total_sqls = repo.count_new_sqls(tenant_id, start_date, end_date)
        mql_count = repo.count_mqls_in_period(tenant_id, start_date, end_date)
        checkout_events = repo.count_checkout_events(tenant_id, start_date, end_date)
        meeting_events = repo.count_meeting_events(tenant_id, start_date, end_date)
        payment_link_events = repo.count_payment_link_events(tenant_id, start_date, end_date)

        # Extract counts
        checkout_count = checkout_events["checkout_initiated"]["count"]
        checkout_value = checkout_events["checkout_initiated"]["value"]
        abandoned_count = checkout_events["cart_abandoned"]["count"]
        abandoned_value = checkout_events["cart_abandoned"]["value"]

        meeting_booked = meeting_events["booked"]
        meeting_completed = meeting_events["completed"]
        meeting_no_show = meeting_events["no_show"]
        meeting_rescheduled = meeting_events["rescheduled"]

        payment_count = payment_link_events["count"]
        payment_value = payment_link_events["value"]

        # 4. Calculate header KPIs
        conversion_rate = round(total_sqls / mql_count * 100, 2) if mql_count > 0 else 0.0

        cost_svc = StageCostService(self.db)
        total_cost = sum(cost_svc.get_channel_costs(tenant_id, "opportunity").values())
        cost_per_sql = cost_svc.calculate_cost_per_mql(total_cost, total_sqls)

        # 5. Build channel groups
        groups: Dict[str, List[ChannelMetricDTO]] = {
            "checkout": [],
            "payment_links": [],
            "qualification": [],
        }
        available_channels: List[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            channel_type = ch["channel_type"]
            group_key = _OPPORTUNITY_GROUP_MAP.get(channel_type, "checkout")

            metrics: List[MetricValueDTO] = []

            if slug == "checkout-init":
                metrics = [
                    MetricValueDTO(name="count", value=float(checkout_count)),
                    MetricValueDTO(name="value", value=checkout_value, unit="currency", currency="USD"),
                ]
            elif slug == "abandoned-cart":
                abandonment_rate = round(abandoned_count / checkout_count * 100, 2) if checkout_count > 0 else 0.0
                metrics = [
                    MetricValueDTO(name="count", value=float(abandoned_count)),
                    MetricValueDTO(name="value", value=abandoned_value, unit="currency", currency="USD"),
                    MetricValueDTO(name="abandonment_rate", value=abandonment_rate, unit="percentage"),
                ]
            elif slug == "link-enviado":
                metrics = [
                    MetricValueDTO(name="count", value=float(payment_count)),
                    MetricValueDTO(name="value", value=payment_value, unit="currency", currency="USD"),
                ]
            elif slug == "checkout-lp":
                # Landing page checkout -- Proximamente
                metrics = [
                    MetricValueDTO(name="count", value=0.0),
                    MetricValueDTO(name="value", value=0.0, unit="currency", currency="USD"),
                ]
            elif slug == "meeting-booked":
                metrics = [
                    MetricValueDTO(name="booked", value=float(meeting_booked)),
                    MetricValueDTO(name="completed", value=float(meeting_completed)),
                    MetricValueDTO(name="no_show", value=float(meeting_no_show)),
                    MetricValueDTO(name="rescheduled", value=float(meeting_rescheduled)),
                ]

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
            )
            groups[group_key].append(dto)

        # Available (unconnected) channels
        for ch in channel_split.get("available", []):
            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                metrics=[],
                source_label=ch["source_label"],
                connected=False,
            )
            available_channels.append(dto)

        # 6. Compute group totals
        def _compute_totals(channels: List[ChannelMetricDTO]) -> Dict[str, float]:
            totals: Dict[str, float] = defaultdict(float)
            for ch_dto in channels:
                for m in ch_dto.metrics:
                    totals[m.name] += m.value
            return dict(totals)

        # 7. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        # Abandoned cart rate
        if checkout_count > 0:
            abandon_rate = (abandoned_count / checkout_count) * 100
            if abandon_rate > 50:
                bottlenecks.append(BottleneckDTO(
                    type="abandoned_cart",
                    metric_label="Tasa de Abandono",
                    current_rate=round(abandon_rate, 1),
                    severity="critical",
                    threshold=50.0,
                    tip="Revisa tu proceso de pago y considera email de recuperacion de carrito",
                ))
            elif abandon_rate > 30:
                bottlenecks.append(BottleneckDTO(
                    type="abandoned_cart",
                    metric_label="Tasa de Abandono",
                    current_rate=round(abandon_rate, 1),
                    severity="warning",
                    threshold=30.0,
                    tip="Revisa tu proceso de pago y considera email de recuperacion de carrito",
                ))

        # Meeting no-show rate
        if meeting_booked > 0:
            no_show_rate = (meeting_no_show / meeting_booked) * 100
            if no_show_rate > 40:
                bottlenecks.append(BottleneckDTO(
                    type="meeting_no_show",
                    metric_label="Tasa de No-Show",
                    current_rate=round(no_show_rate, 1),
                    severity="critical",
                    threshold=40.0,
                    tip="Considera recordatorios automaticos antes de la reunion",
                ))
            elif no_show_rate > 20:
                bottlenecks.append(BottleneckDTO(
                    type="meeting_no_show",
                    metric_label="Tasa de No-Show",
                    current_rate=round(no_show_rate, 1),
                    severity="warning",
                    threshold=20.0,
                    tip="Considera recordatorios automaticos antes de la reunion",
                ))

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        now = dt_cls.now(tz.utc)

        result = OpportunityDetailDTO(
            header_kpis=OpportunityHeaderKpisDTO(
                total_sqls=total_sqls,
                conversion_rate=conversion_rate,
                cost_per_sql=cost_per_sql,
            ),
            mini_funnel=MiniFunnelDTO(
                source_label="MQLs",
                source_value=mql_count,
                target_label="SQLs",
                target_value=total_sqls,
                conversion_rate=conversion_rate,
            ),
            checkout=TrafficGroupDTO(
                totals=_compute_totals(groups["checkout"]),
                channels=groups["checkout"],
            ),
            payment_links=TrafficGroupDTO(
                totals=_compute_totals(groups["payment_links"]),
                channels=groups["payment_links"],
            ),
            qualification=TrafficGroupDTO(
                totals=_compute_totals(groups["qualification"]),
                channels=groups["qualification"],
            ),
            bottlenecks=bottlenecks,
            available=available_dto,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "opportunity",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_sales_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> SalesDetailDTO:
        """Return sales-stage (Stage 4) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for sales stage)
        2. On miss: query SalesMetricsRepository for raw aggregations
        3. Query OfferReadPort for offer enrichment (names, value_levels, pricing_type)
        4. Group sales by stage (CONVERSION->adquisicion, EXPANSION->expansion)
        5. Sub-group by tier using get_tier_for_value_level
        6. Build per-offer OfferSaleDTOs with source breakdown and subscription split
        7. Calculate header KPIs (revenue, new_customers, CAC)
        8. Build mini funnel (SQLs -> Customers)
        9. Detect bottlenecks (low_conversion_rate, high_cac_ratio)
        10. Cache result and return SalesDetailDTO
        """
        from datetime import datetime as dt_cls, timezone as tz
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "sales", "last_30_days"
            )
            if cached is not None:
                return SalesDetailDTO(**cached)

        # 2. Query raw sales aggregations
        sales_repo = SalesMetricsRepository(self.db)
        raw_sales = sales_repo.get_sales_summary(tenant_id, start_date, end_date)

        # 3. Get all offers for enrichment via OfferReadPort
        offer_map = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_map = {str(o.id): o for o in offers}

        # 4. Group sales by stage -> offer_id -> accumulate
        # Structure: {stage_key: {offer_id_str: {source: str, counts/revenue}}}
        stage_data: Dict[str, Dict[str, Dict[str, Any]]] = {
            "adquisicion": {},
            "expansion": {},
        }

        # Track per-stage customer counts and revenue totals
        stage_customer_counts: Dict[str, int] = {"adquisicion": 0, "expansion": 0}
        stage_revenue: Dict[str, float] = {"adquisicion": 0.0, "expansion": 0.0}

        for row in raw_sales:
            # row: (stage, offer_id, source, currency, count, total_revenue, unique_customers)
            stage_val = row[0]
            offer_id = str(row[1])
            source = row[2] or "MANUAL"
            currency = row[3] or "USD"
            count = int(row[4])
            revenue = float(row[5])
            unique_custs = int(row[6])

            # Map SaleStage to group key
            stage_str = stage_val.value if hasattr(stage_val, "value") else str(stage_val)
            if stage_str == "CONVERSION":
                stage_key = "adquisicion"
            elif stage_str == "EXPANSION":
                stage_key = "expansion"
            else:
                continue

            if offer_id not in stage_data[stage_key]:
                stage_data[stage_key][offer_id] = {
                    "count": 0,
                    "revenue": 0.0,
                    "currency": currency,
                    "sources": defaultdict(int),
                    "unique_customers": 0,
                }

            entry = stage_data[stage_key][offer_id]
            entry["count"] += count
            entry["revenue"] += revenue
            entry["sources"][source] += count
            entry["unique_customers"] += unique_custs
            stage_revenue[stage_key] += revenue

        # 5. Also include unsold offers from the catalog (show with $0)
        for offer_id_str, offer in offer_map.items():
            for stage_key in ("adquisicion", "expansion"):
                if offer_id_str not in stage_data[stage_key]:
                    # Only add to adquisicion for unsold offers
                    if stage_key == "adquisicion":
                        stage_data[stage_key][offer_id_str] = {
                            "count": 0,
                            "revenue": 0.0,
                            "currency": offer.currency,
                            "sources": {},
                            "unique_customers": 0,
                        }

        # Determine tenant display currency (most common from sales)
        currency_counts: Dict[str, int] = defaultdict(int)
        for row in raw_sales:
            currency_counts[row[3] or "USD"] += int(row[4])
        display_currency = max(currency_counts, key=currency_counts.get) if currency_counts else "USD"

        # 6. Build RevenueGroupDTO for each stage
        total_revenue_all = sum(stage_revenue.values())

        def _build_revenue_group(
            stage_key: str, group_label: str
        ) -> RevenueGroupDTO:
            offers_by_tier: Dict[str, List[OfferSaleDTO]] = defaultdict(list)
            group_revenue = stage_revenue[stage_key]
            group_customers = 0

            for offer_id_str, data in stage_data[stage_key].items():
                offer = offer_map.get(offer_id_str)

                # Determine tier
                value_level = offer.value_level if offer else None
                tier = get_tier_for_value_level(value_level)

                # Skip free tier offers (level_0)
                if value_level and value_level == "level_0_free":
                    continue

                # Build OfferSaleDTO
                offer_name = offer.public_name if offer else f"Oferta {offer_id_str[:8]}"
                offer_type = offer.offer_type if offer else "unknown"
                pricing_type = offer.pricing_type if offer else "one_time"
                offer_currency = data["currency"]

                usd_revenue = convert_to_usd(data["revenue"], offer_currency)

                # Subscription split
                new_subs = None
                new_sub_rev = None
                renewals = None
                renewal_rev = None
                sub_new_label = None
                sub_renewal_label = None

                labels = get_subscription_labels(pricing_type, offer_type)
                if labels is not None:
                    if stage_key == "adquisicion":
                        new_subs = data["count"]
                        new_sub_rev = data["revenue"]
                    else:  # expansion
                        renewals = data["count"]
                        renewal_rev = data["revenue"]
                    sub_new_label = labels.get("new_label")
                    sub_renewal_label = labels.get("renewal_label")

                offer_dto = OfferSaleDTO(
                    offer_id=offer_id_str,
                    public_name=offer_name,
                    offer_type=offer_type,
                    pricing_type=pricing_type,
                    total_revenue=data["revenue"],
                    sales_count=data["count"],
                    currency=offer_currency,
                    usd_revenue=usd_revenue,
                    source_breakdown=dict(data["sources"]),
                    new_subscriptions=new_subs,
                    new_subscription_revenue=new_sub_rev,
                    renewals=renewals,
                    renewal_revenue=renewal_rev,
                    subscription_new_label=sub_new_label,
                    subscription_renewal_label=sub_renewal_label,
                )
                offers_by_tier[tier].append(offer_dto)
                group_customers += data["unique_customers"]

            # Build TierGroupDTOs in display order
            tiers = []
            for tier_key in TIER_DISPLAY_ORDER:
                if tier_key in offers_by_tier:
                    tiers.append(TierGroupDTO(
                        tier_key=tier_key,
                        tier_label=TIER_LABELS[tier_key],
                        offers=offers_by_tier[tier_key],
                    ))

            rev_pct = round(group_revenue / total_revenue_all * 100, 1) if total_revenue_all > 0 else 0.0
            group_usd = convert_to_usd(group_revenue, display_currency)

            return RevenueGroupDTO(
                group_key=stage_key,
                group_label=group_label,
                total_revenue=group_revenue,
                total_revenue_usd=group_usd,
                customer_count=group_customers,
                revenue_percentage=rev_pct,
                currency=display_currency,
                tiers=tiers,
            )

        adquisicion = _build_revenue_group("adquisicion", "Adquisicion")
        expansion = _build_revenue_group("expansion", "Expansion")

        # 7. Header KPIs
        new_customers = sales_repo.get_total_conversion_customers(
            tenant_id, start_date, end_date
        )

        cost_svc = StageCostService(self.db)
        total_investment, cost_complete = cost_svc.get_total_funnel_investment(
            tenant_id, start_date, end_date
        )
        cac = round(total_investment / new_customers, 2) if new_customers > 0 else None
        cac_incomplete = not cost_complete

        total_rev = total_revenue_all
        total_rev_usd = convert_to_usd(total_rev, display_currency)

        header_kpis = SalesHeaderKpisDTO(
            total_revenue=total_rev,
            total_revenue_usd=total_rev_usd,
            currency=display_currency,
            new_customers=new_customers,
            cac=cac,
            cac_incomplete=cac_incomplete,
        )

        # 8. Mini funnel: SQLs -> Customers
        sql_count = sales_repo.get_total_sql_count(tenant_id, start_date, end_date)
        conv_rate = round(new_customers / sql_count * 100, 2) if sql_count > 0 else 0.0

        mini_funnel = MiniFunnelDTO(
            source_label="Oportunidades",
            source_value=sql_count,
            target_label="Ventas",
            target_value=new_customers,
            conversion_rate=conv_rate,
        )

        # 9. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        # Low conversion rate (SQL -> Customer)
        if sql_count > 0:
            if conv_rate < LOW_CONVERSION_THRESHOLDS["critical"]:
                bottlenecks.append(BottleneckDTO(
                    type="low_conversion_rate",
                    metric_label="Tasa de Conversion",
                    current_rate=conv_rate,
                    severity="critical",
                    threshold=LOW_CONVERSION_THRESHOLDS["critical"],
                    tip="Baja conversion de oportunidades a ventas -- revisa tu proceso de cierre",
                ))
            elif conv_rate < LOW_CONVERSION_THRESHOLDS["warning"]:
                bottlenecks.append(BottleneckDTO(
                    type="low_conversion_rate",
                    metric_label="Tasa de Conversion",
                    current_rate=conv_rate,
                    severity="warning",
                    threshold=LOW_CONVERSION_THRESHOLDS["warning"],
                    tip="Baja conversion de oportunidades a ventas -- revisa tu proceso de cierre",
                ))

        # High CAC ratio (CAC / AOV)
        if cac is not None and new_customers > 0 and total_rev > 0:
            aov = total_rev / new_customers
            cac_ratio = cac / aov if aov > 0 else 0.0
            if cac_ratio >= HIGH_CAC_CRITICAL_RATIO:
                bottlenecks.append(BottleneckDTO(
                    type="high_cac_ratio",
                    metric_label="CAC / Ticket Promedio",
                    current_rate=round(cac_ratio * 100, 1),
                    severity="critical",
                    threshold=HIGH_CAC_CRITICAL_RATIO * 100,
                    tip="Tu costo de adquisicion es alto respecto al ticket promedio -- optimiza tu funnel pre-venta",
                ))
            elif cac_ratio >= HIGH_CAC_WARNING_RATIO:
                bottlenecks.append(BottleneckDTO(
                    type="high_cac_ratio",
                    metric_label="CAC / Ticket Promedio",
                    current_rate=round(cac_ratio * 100, 1),
                    severity="warning",
                    threshold=HIGH_CAC_WARNING_RATIO * 100,
                    tip="Tu costo de adquisicion es alto respecto al ticket promedio -- optimiza tu funnel pre-venta",
                ))

        now = dt_cls.now(tz.utc)

        result = SalesDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            adquisicion=adquisicion,
            expansion=expansion,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 10. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "sales",
                "last_30_days",
                result.model_dump(),
            )

        return result
