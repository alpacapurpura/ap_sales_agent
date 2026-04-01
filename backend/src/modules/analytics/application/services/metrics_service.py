"""MetricsService -- dashboard data for marketing funnel visualization.

get_attraction_metrics() reads from ETL official tables via:
- MetricsCache (5-min Redis TTL)
- OfficialMetricsRepository / MetricAggregationModel
- ChannelRegistry (dynamic channel list from ConnectionPort)

get_marketing_sankey_metrics() still reads from journey_events (separate migration).
"""

from collections import defaultdict
from datetime import datetime
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
from src.modules.analytics.application.dto.adoption_dto import (
    AdoptionDetailDTO,
    AdoptionHeaderKpisDTO,
    OfferHealthDTO,
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
from src.modules.analytics.application.dto.expansion_dto import (
    ExpansionDetailDTO,
    ExpansionHeaderKpisDTO,
    ExpansionGroupDTO,
    ExpansionOfferDTO,
)
from src.modules.analytics.application.dto.evangelization_dto import (
    EvangelizationDetailDTO,
    EvangelizationHeaderKpisDTO,
    EvangelistDTO,
    CandidatoDTO,
    NpsSummaryDTO,
)
from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from src.modules.analytics.application.dto.timeseries_dto import (
    ChannelInfoDTO,
    StageTimeSeriesDTO,
    TimeSeriesPointDTO,
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
from src.modules.analytics.application.services.aggregation_helpers import compute_channel_totals

# Maps our channel slugs to the ChannelType enum for connection lookups (sankey legacy)
_CHANNEL_CONNECTION_MAP: Dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,
    "yt-ads": ChannelType.YOUTUBE,
}

# Channel types -> group mapping for the 5-group structure
_GROUP_MAP: Dict[str, str] = {
    "social": "organic_social",
    "search": "ga4_search",
    "direct": "ga4_search",
    "paid": "paid",
    "outbound": "outbound",
    "website": "website",
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

# Maps provider_name -> config key that holds the display name
_DISPLAY_NAME_MAP: Dict[str, str] = {
    "google_analytics": "property_display_name",
    "youtube": "channel_title",
    "meta": "tracked_ig_username",
    "google_ads": "property_display_name",
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
            "website": [],
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

            # For ManyChat channels, read from official_metrics directly
            if provider_name == "manychat":
                from datetime import timedelta, timezone as _tz

                now_mc = datetime.now(_tz.utc)
                mc_metrics = OfficialMetricsRepository(self.db).get_channel_metrics(
                    tenant_id,
                    "manychat",
                    slug,
                    (now_mc - timedelta(days=30)).date(),
                    now_mc.date(),
                )
                existing_names = {m.name for m in metrics}
                for m_name, m_value in mc_metrics.items():
                    if m_name not in existing_names:
                        metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))

            # Resolve display name from connection config
            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = conn_config.get(display_name_key) if display_name_key else None

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
                source_display_name=source_display,
                provider_name=provider_name,
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
        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        website_group = (
            TrafficGroupDTO(
                totals=compute_channel_totals(groups["website"]),
                channels=groups["website"],
            )
            if groups["website"]
            else None
        )

        result = AttractionDetailDTO(
            organic_social=TrafficGroupDTO(
                totals=compute_channel_totals(groups["organic_social"]),
                channels=groups["organic_social"],
            ),
            ga4_search=TrafficGroupDTO(
                totals=compute_channel_totals(groups["ga4_search"]),
                channels=groups["ga4_search"],
            ),
            paid=TrafficGroupDTO(
                totals=compute_channel_totals(groups["paid"]),
                channels=groups["paid"],
            ),
            outbound=TrafficGroupDTO(
                totals=compute_channel_totals(groups["outbound"]),
                channels=groups["outbound"],
            ),
            website=website_group,
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

            # For ManyChat channels, supplement with metrics from official_metrics
            provider_name = ch.get("provider_name", "")
            if provider_name == "manychat":
                official_repo = OfficialMetricsRepository(self.db)
                mc_metrics = official_repo.get_channel_metrics(
                    tenant_id,
                    "manychat",
                    slug,
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    end_date.date() if hasattr(end_date, "date") else end_date,
                )
                existing_names = {m.name for m in metrics}
                for m_name, m_value in mc_metrics.items():
                    if m_name not in existing_names:
                        metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))

            # For email_marketing channels, supplement with MailerLite official_metrics
            if provider_name == "email_marketing":
                official_repo = OfficialMetricsRepository(self.db)
                ml_metrics = official_repo.get_channel_metrics(
                    tenant_id,
                    "mailerlite",
                    slug,
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    end_date.date() if hasattr(end_date, "date") else end_date,
                )
                existing_names = {m.name for m in metrics}
                # Use new_subscribers as "leads" if CRM has no data
                ns = ml_metrics.get("new_subscribers", 0)
                if lead_count == 0 and ns > 0:
                    metrics = [m for m in metrics if m.name != "leads"]
                    metrics.insert(0, MetricValueDTO(name="leads", value=float(ns)))
                for m_name, m_value in ml_metrics.items():
                    if m_name not in existing_names and m_name != "new_subscribers":
                        metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))

            # Resolve display name from connection config
            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = conn_config.get(display_name_key) if display_name_key else None

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
                cost_type="EXPENSE",
                source_display_name=source_display,
                provider_name=provider_name,
            )
            groups[group_key].append(dto)

        # Merge manychat-ig into ig-dm as a unified card with sub_sources
        detailed_leads = capture_repo.count_leads_by_source_detailed(
            tenant_id, start_date, end_date
        )
        self._merge_manychat_into_meta(
            groups["ai_agent"], detailed_leads, conversation_counts
        )

        # Available (unconnected) channels — remove manychat-ig/wa if merged
        merged_slugs = {"manychat-ig", "manychat-wa"}
        for ch in channel_split.get("available", []):
            if ch["slug"] in merged_slugs:
                continue
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
                totals=compute_channel_totals(groups["web_infrastructure"]),
                channels=groups["web_infrastructure"],
            ),
            ai_agent=TrafficGroupDTO(
                totals=compute_channel_totals(groups["ai_agent"]),
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

    @staticmethod
    def _merge_manychat_into_meta(
        channels: List[ChannelMetricDTO],
        detailed_leads: Dict[str, int],
        conversation_counts: Dict[str, int],
    ) -> None:
        """Merge manychat-ig into ig-dm as a unified card (in-place).

        When both ig-dm and manychat-ig exist in the channel list, the
        manychat-ig card is removed and the ig-dm card gets sub_sources
        showing the per-source breakdown.
        """
        from src.modules.analytics.application.dto.attraction_dto import SubSourceDTO

        # Pair: (meta_slug, manychat_slug)
        merge_pairs = [
            ("ig-dm", "manychat-ig"),
            ("whatsapp-inbound", "manychat-wa"),
        ]

        for meta_slug, mc_slug in merge_pairs:
            meta_dto = next((c for c in channels if c.slug == meta_slug), None)
            mc_dto = next((c for c in channels if c.slug == mc_slug), None)

            if not meta_dto or not mc_dto:
                continue

            # Build sub_sources from raw (unconsolidated) counts
            meta_leads = detailed_leads.get(meta_slug, 0)
            mc_leads = detailed_leads.get(mc_slug, 0)
            meta_convs = conversation_counts.get(meta_slug, 0)
            mc_convs = conversation_counts.get(mc_slug, 0)

            meta_dto.sub_sources = [
                SubSourceDTO(name="Meta Direct", leads=meta_leads, conversations=meta_convs),
                SubSourceDTO(name="ManyChat", leads=mc_leads, conversations=mc_convs),
            ]

            # Append ManyChat-exclusive metrics to the unified card
            existing_names = {m.name for m in meta_dto.metrics}
            for m in mc_dto.metrics:
                if m.name not in existing_names:
                    meta_dto.metrics.append(m)

            # Remove the standalone manychat card
            channels.remove(mc_dto)

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

            if slug == "email-nurture":
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

            # For ManyChat channels, supplement with metrics from official_metrics
            provider_name = ch.get("provider_name", "")
            if provider_name == "manychat":
                mc_metrics_nurture = OfficialMetricsRepository(self.db).get_channel_metrics(
                    tenant_id,
                    "manychat",
                    slug,
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    now.date() if hasattr(now, "date") else now,
                )
                existing_names = {m.name for m in metrics}
                for m_name, m_value in mc_metrics_nurture.items():
                    if m_name not in existing_names:
                        metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))

            # Resolve display name from connection config
            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = conn_config.get(display_name_key) if display_name_key else None

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
                source_display_name=source_display,
                provider_name=provider_name,
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
        retargeting_totals = compute_channel_totals(groups["retargeting"])
        if retargeting_cost_per_mql is not None:
            retargeting_totals["cost_per_mql"] = retargeting_cost_per_mql

        automation_totals = compute_channel_totals(groups["automation"])
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
        from datetime import datetime as dt_cls, timezone as tz

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

            # For ManyChat channels, supplement with metrics from official_metrics
            provider_name = ch.get("provider_name", "")
            if provider_name == "manychat":
                mc_metrics_opp = OfficialMetricsRepository(self.db).get_channel_metrics(
                    tenant_id,
                    "manychat",
                    slug,
                    start_date.date() if hasattr(start_date, "date") else start_date,
                    end_date.date() if hasattr(end_date, "date") else end_date,
                )
                existing_names = {m.name for m in metrics}
                for m_name, m_value in mc_metrics_opp.items():
                    if m_name not in existing_names:
                        metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))

            # Resolve display name from connection config
            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = conn_config.get(display_name_key) if display_name_key else None

            dto = ChannelMetricDTO(
                slug=slug,
                name=ch["name"],
                channel_type=channel_type,
                metrics=metrics,
                source_label=ch["source_label"],
                connected=True,
                source_display_name=source_display,
                provider_name=provider_name,
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
                totals=compute_channel_totals(groups["checkout"]),
                channels=groups["checkout"],
            ),
            payment_links=TrafficGroupDTO(
                totals=compute_channel_totals(groups["payment_links"]),
                channels=groups["payment_links"],
            ),
            qualification=TrafficGroupDTO(
                totals=compute_channel_totals(groups["qualification"]),
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
        _stage_customer_counts: Dict[str, int] = {"adquisicion": 0, "expansion": 0}
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

                # Skip lead magnets (don't generate revenue)
                if value_level and value_level in ("lead_magnet", "level_0_free"):
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

        # Enrich with Shopify metrics from official_metrics
        official_repo = OfficialMetricsRepository(self.db)
        shopify_agg = official_repo.get_channel_metrics(
            tenant_id, "shopify", "shopify", start_date.date(), end_date.date(),
        )

        # Extract Shopify aggregates
        shopify_revenue = shopify_agg.get("revenue", 0.0)
        shopify_order_count = int(shopify_agg.get("order_count", 0))
        shopify_avg_order = shopify_agg.get("avg_order_value", 0.0)

        # Determine Shopify currency from stored metrics
        shopify_currency = display_currency
        if shopify_revenue > 0:
            sample_rows = official_repo.get_metrics(
                tenant_id, channel_slug="shopify", metric_name="revenue",
                start_date=start_date.date(), end_date=end_date.date(),
            )
            if sample_rows:
                shopify_currency = sample_rows[0].currency or "USD"
                if not currency_counts:
                    display_currency = shopify_currency

        # FALLBACK: when CRM has no revenue, use Shopify as primary
        if total_rev == 0 and shopify_revenue > 0:
            total_rev = shopify_revenue
            total_rev_usd = convert_to_usd(shopify_revenue, shopify_currency)
        if new_customers == 0 and shopify_order_count > 0:
            new_customers = shopify_order_count
            # Recalculate CAC with updated new_customers
            if total_investment > 0 and new_customers > 0:
                cac = round(total_investment / new_customers, 2)

        header_kpis = SalesHeaderKpisDTO(
            total_revenue=total_rev,
            total_revenue_usd=total_rev_usd,
            currency=display_currency,
            new_customers=new_customers,
            cac=cac,
            cac_incomplete=cac_incomplete,
            net_sales=shopify_agg.get("net_sales", 0.0),
            total_discounts=shopify_agg.get("total_discounts", 0.0),
            total_tax=shopify_agg.get("total_tax", 0.0),
            refund_count=int(shopify_agg.get("refund_count", 0)),
            refund_amount=shopify_agg.get("refund_amount", 0.0),
            shipping_revenue=shopify_agg.get("shipping_revenue", 0.0),
            repeat_customers=int(shopify_agg.get("repeat_customers", 0)),
            discount_usage_count=int(shopify_agg.get("discount_usage_count", 0)),
            shopify_revenue=shopify_revenue,
            shopify_order_count=shopify_order_count,
            shopify_avg_order_value=shopify_avg_order,
            shopify_currency=shopify_currency,
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

    async def get_adoption_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> AdoptionDetailDTO:
        """Return adoption-stage (Stage 5) metrics.

        Flow:
        1. Check MetricsCache
        2. On miss: query AdoptionMetricsRepository for health, TTV, refunds
        3. Query OfferReadPort for offer name enrichment
        4. Build per-offer OfferHealthDTOs
        5. Calculate header KPIs (distinct customer counts, not per-offer sums)
        6. Build mini funnel (Ventas -> Activos)
        7. Detect bottlenecks (overall health < 70%, per-offer health < 60%)
        8. Cache result and return AdoptionDetailDTO
        """
        from datetime import datetime as dt_cls, timezone as tz
        from src.modules.analytics.infrastructure.repositories.adoption_repository import (
            AdoptionMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "adoption", "last_30_days"
            )
            if cached is not None:
                return AdoptionDetailDTO(**cached)

        # 2. Query repository
        repo = AdoptionMetricsRepository(self.db)
        health_rows = repo.get_customer_health_by_offer(
            tenant_id, start_date, end_date
        )
        ttv_map = repo.get_avg_ttv_by_offer(tenant_id, start_date, end_date)
        total_customers, total_sales = repo.get_total_customers_and_sales(
            tenant_id, start_date, end_date
        )
        refund_count, refund_amount, refund_currency = repo.get_refunds(
            tenant_id, start_date, end_date
        )

        # 3. Get offer names via OfferReadPort
        offer_name_map: Dict[str, str] = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_name_map = {str(o.id): o.public_name for o in offers}

        # 4. Build per-offer OfferHealthDTOs
        offer_list: List[OfferHealthDTO] = []
        for row in health_rows:
            offer_id_str = str(row[0])
            total = int(row[1])
            active = int(row[2])
            inactive = int(row[3])
            health = round(active / total * 100, 1) if total > 0 else 0.0
            public_name = offer_name_map.get(offer_id_str, "Oferta")

            offer_list.append(
                OfferHealthDTO(
                    offer_id=offer_id_str,
                    public_name=public_name,
                    total_customers=total,
                    active_count=active,
                    inactive_count=inactive,
                    health_pct=health,
                    ttv_days=ttv_map.get(offer_id_str),
                )
            )

        # 5. Header KPIs -- use distinct total counts (avoid double-counting)
        total_active_per_offer = sum(int(row[2]) for row in health_rows)
        total_inactive_per_offer = sum(int(row[3]) for row in health_rows)

        # If per-offer sums exceed distinct total, customer bought multiple offers
        if total_active_per_offer + total_inactive_per_offer > total_customers and total_customers > 0:
            active_customers = total_customers - total_inactive_per_offer
            if active_customers < 0:
                active_customers = 0
            inactive_customers = total_customers - active_customers
        else:
            active_customers = total_active_per_offer
            inactive_customers = total_inactive_per_offer

        health_pct = (
            round(active_customers / total_customers * 100, 1)
            if total_customers > 0
            else 0.0
        )

        # Global avg TTV
        all_ttvs = list(ttv_map.values())
        avg_ttv = (
            round(sum(all_ttvs) / len(all_ttvs), 1) if all_ttvs else None
        )

        refund_amount_usd = convert_to_usd(refund_amount, refund_currency)

        header_kpis = AdoptionHeaderKpisDTO(
            active_customers=active_customers,
            inactive_customers=inactive_customers,
            health_pct=health_pct,
            avg_ttv_days=avg_ttv,
            refund_count=refund_count,
            refund_amount=refund_amount,
            refund_currency=refund_currency,
            refund_amount_usd=refund_amount_usd,
        )

        # 6. Mini funnel: Ventas -> Activos
        conv_rate = (
            round(active_customers / total_sales * 100, 1)
            if total_sales > 0
            else 0.0
        )
        mini_funnel = MiniFunnelDTO(
            source_label="Ventas",
            source_value=total_sales,
            target_label="Activos",
            target_value=active_customers,
            conversion_rate=conv_rate,
        )

        # 7. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        # Overall health bottleneck
        if health_pct < 70.0:
            if avg_ttv is not None and avg_ttv > 7:
                tip = (
                    "Mejora tu proceso de bienvenida -- tus clientes tardan "
                    "mucho en empezar a usar tu producto"
                )
            else:
                tip = (
                    "Contacta a tus clientes inactivos con un mensaje "
                    "personalizado o una oferta especial para reactivarlos"
                )
            bottlenecks.append(
                BottleneckDTO(
                    type="low_adoption_health",
                    metric_label="Salud del cliente",
                    current_rate=health_pct,
                    severity="warning",
                    threshold=70.0,
                    tip=tip,
                )
            )

        # Per-offer bottleneck
        for offer in offer_list:
            if offer.health_pct < 60.0:
                bottlenecks.append(
                    BottleneckDTO(
                        type="offer_low_health",
                        metric_label=f"Salud: {offer.public_name}",
                        current_rate=offer.health_pct,
                        severity="warning",
                        threshold=60.0,
                        tip=(
                            "Revisa el engagement de este producto -- mas de "
                            "la mitad de sus clientes estan inactivos"
                        ),
                    )
                )

        now = dt_cls.now(tz.utc)

        result = AdoptionDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            offers=offer_list,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "adoption",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_expansion_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> ExpansionDetailDTO:
        """Return expansion-stage (Stage 6) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for expansion stage)
        2. On miss: query ExpansionMetricsRepository for renewal/upsell/churn data
        3. Query OfferReadPort for offer name enrichment
        4. Build three ExpansionGroupDTOs: retencion, crecimiento, cancelaciones
        5. Calculate header KPIs (Net MRR, Avg LTV, Churn Rate)
        6. Build mini funnel (Activos -> Expansion)
        7. Detect bottlenecks (churn rate > 3% warning, > 5% critical)
        8. Cache result and return ExpansionDetailDTO
        """
        from datetime import datetime as dt_cls, timezone as tz
        from src.modules.analytics.infrastructure.repositories.expansion_repository import (
            ExpansionMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "expansion", "last_30_days"
            )
            if cached is not None:
                return ExpansionDetailDTO(**cached)

        # 2. Query expansion data
        exp_repo = ExpansionMetricsRepository(self.db)
        sales_grouped = exp_repo.get_expansion_sales_grouped(
            tenant_id, start_date, end_date
        )
        churn_by_offer = exp_repo.get_churn_data_by_offer(
            tenant_id, start_date, end_date
        )
        total_churn_count = exp_repo.get_total_churn_count(
            tenant_id, start_date, end_date
        )
        active_customer_count = exp_repo.get_active_customer_count(tenant_id)
        avg_ltv, ltv_currency = exp_repo.get_avg_ltv(tenant_id)
        upsell_customer_count = exp_repo.get_expansion_customer_count(
            tenant_id, start_date, end_date
        )

        # 3. Get offers for enrichment
        offer_map = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_map = {str(o.id): o for o in offers}

        # Determine display currency from first sale found
        display_currency = "MXN"
        renewals = sales_grouped.get("renewals", [])
        upsells = sales_grouped.get("upsells", [])
        if renewals:
            display_currency = renewals[0][3]
        elif upsells:
            display_currency = upsells[0][3]

        # 4. Build ExpansionGroupDTOs

        def _build_offers(
            raw_items: List[tuple], is_churn: bool = False
        ) -> List[ExpansionOfferDTO]:
            result_offers = []
            for item in raw_items:
                offer_id_str = str(item[0])
                count = item[1]
                revenue = item[2]
                currency = item[3] if len(item) > 3 else display_currency
                offer = offer_map.get(offer_id_str)
                name = offer.public_name if offer else f"Oferta {offer_id_str[:8]}"
                usd_rev = convert_to_usd(revenue, currency)
                result_offers.append(ExpansionOfferDTO(
                    offer_id=offer_id_str,
                    public_name=name,
                    count=count,
                    revenue=revenue,
                    currency=currency,
                    usd_revenue=usd_rev,
                ))
            return result_offers

        # Retencion group (renewals)
        renewal_offers = _build_offers(renewals)
        renewal_total_count = sum(o.count for o in renewal_offers)
        renewal_total_revenue = sum(o.revenue for o in renewal_offers)
        retention_rate = (
            round((active_customer_count - total_churn_count) / active_customer_count * 100, 1)
            if active_customer_count > 0
            else 100.0
        )

        retencion = ExpansionGroupDTO(
            group_key="retencion",
            group_label="Retencion",
            group_subtitle="Renovaciones de suscripciones activas",
            total_count=renewal_total_count,
            total_revenue=renewal_total_revenue,
            total_revenue_usd=convert_to_usd(renewal_total_revenue, display_currency),
            currency=display_currency,
            rate_pct=retention_rate,
            offers=renewal_offers,
        )

        # Crecimiento group (upsells)
        upsell_offers = _build_offers(upsells)
        upsell_total_count = sum(o.count for o in upsell_offers)
        upsell_total_revenue = sum(o.revenue for o in upsell_offers)
        expansion_rate = (
            round(upsell_customer_count / active_customer_count * 100, 1)
            if active_customer_count > 0
            else 0.0
        )

        crecimiento = ExpansionGroupDTO(
            group_key="crecimiento",
            group_label="Crecimiento",
            group_subtitle="Ventas adicionales y upgrades a clientes existentes",
            total_count=upsell_total_count,
            total_revenue=upsell_total_revenue,
            total_revenue_usd=convert_to_usd(upsell_total_revenue, display_currency),
            currency=display_currency,
            rate_pct=expansion_rate,
            offers=upsell_offers,
        )

        # Cancelaciones group (churn)
        churn_offers = _build_offers(churn_by_offer, is_churn=True)
        churn_total_count = total_churn_count
        churn_total_revenue = sum(o.revenue for o in churn_offers)
        churn_rate_pct = (
            round(total_churn_count / active_customer_count * 100, 1)
            if active_customer_count > 0
            else 0.0
        )

        cancelaciones = ExpansionGroupDTO(
            group_key="cancelaciones",
            group_label="Cancelaciones",
            group_subtitle="Suscripciones perdidas y ingreso afectado",
            total_count=churn_total_count,
            total_revenue=churn_total_revenue,
            total_revenue_usd=convert_to_usd(churn_total_revenue, display_currency),
            currency=display_currency,
            rate_pct=churn_rate_pct,
            offers=churn_offers,
        )

        # 5. Header KPIs
        net_mrr = renewal_total_revenue + upsell_total_revenue - churn_total_revenue
        net_mrr_usd = convert_to_usd(net_mrr, display_currency)
        avg_ltv_usd = convert_to_usd(avg_ltv, ltv_currency)

        header_kpis = ExpansionHeaderKpisDTO(
            net_mrr=net_mrr,
            net_mrr_usd=net_mrr_usd,
            currency=display_currency,
            avg_ltv=avg_ltv,
            avg_ltv_usd=avg_ltv_usd,
            churn_rate_pct=churn_rate_pct,
        )

        # 6. Mini funnel: Activos -> Expansion
        total_expansion_count = renewal_total_count + upsell_total_count
        expansion_conv_rate = (
            round(total_expansion_count / active_customer_count * 100, 1)
            if active_customer_count > 0
            else 0.0
        )

        mini_funnel = MiniFunnelDTO(
            source_label="Activos",
            source_value=active_customer_count,
            target_label="Expansion",
            target_value=total_expansion_count,
            conversion_rate=expansion_conv_rate,
        )

        # 7. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        if churn_rate_pct > 5.0:
            tip = "Revisa la calidad y satisfaccion de tu producto o servicio"
            bottlenecks.append(BottleneckDTO(
                type="high_churn_rate",
                metric_label="Tasa de Cancelacion",
                current_rate=churn_rate_pct,
                severity="critical",
                threshold=5.0,
                tip=tip,
            ))
        elif churn_rate_pct > 3.0:
            bottlenecks.append(BottleneckDTO(
                type="high_churn_rate",
                metric_label="Tasa de Cancelacion",
                current_rate=churn_rate_pct,
                severity="warning",
                threshold=3.0,
                tip="Revisa la calidad y satisfaccion de tu producto o servicio",
            ))

        now = dt_cls.now(tz.utc)

        result = ExpansionDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            retencion=retencion,
            crecimiento=crecimiento,
            cancelaciones=cancelaciones,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "expansion",
                "last_30_days",
                result.model_dump(),
            )

        return result

    async def get_evangelization_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> EvangelizationDetailDTO:
        """Return evangelization-stage (Stage 7) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for evangelization stage)
        2. On miss: query EvangelizationRepository for referral/NPS/UGC data
        3. Compute bottlenecks (low K-Factor, low NPS response rate)
        4. Assemble EvangelizationDetailDTO
        5. Cache result and return
        """
        from datetime import datetime as dt_cls, timezone as tz
        from src.modules.analytics.infrastructure.repositories.evangelization_repository import (
            EvangelizationRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "evangelization", "last_30_days"
            )
            if cached is not None:
                return EvangelizationDetailDTO(**cached)

        # 2. Query repository
        repo = EvangelizationRepository(self.db)
        data = await repo.get_evangelization_data(tenant_id, start_date, end_date)

        # 3. Compute bottlenecks
        bottlenecks: list[BottleneckDTO] = []

        k_factor = data.get("k_factor", 0.0)
        if k_factor < 0.5:
            bottlenecks.append(BottleneckDTO(
                type="low_k_factor",
                metric_label="K-Factor bajo",
                current_rate=k_factor,
                severity="critical",
                threshold=0.5,
                tip="Incentiva a tus mejores clientes a compartir su codigo de referido. Ofrece descuentos o beneficios exclusivos.",
            ))
        elif k_factor < 1.0:
            bottlenecks.append(BottleneckDTO(
                type="low_k_factor",
                metric_label="K-Factor bajo",
                current_rate=k_factor,
                severity="warning",
                threshold=1.0,
                tip="Incentiva a tus mejores clientes a compartir su codigo de referido. Ofrece descuentos o beneficios exclusivos.",
            ))

        nps_response_rate = data.get("nps_response_rate_pct", 0.0)
        surveys_sent = data.get("surveys_sent", 0)
        if surveys_sent > 0:
            if nps_response_rate < 15:
                bottlenecks.append(BottleneckDTO(
                    type="low_nps_response",
                    metric_label="Pocas respuestas NPS",
                    current_rate=nps_response_rate,
                    severity="critical",
                    threshold=15,
                    tip="Envia mas encuestas de satisfaccion. Los clientes que responden tienden a ser tus mejores promotores.",
                ))
            elif nps_response_rate < 30:
                bottlenecks.append(BottleneckDTO(
                    type="low_nps_response",
                    metric_label="Pocas respuestas NPS",
                    current_rate=nps_response_rate,
                    severity="warning",
                    threshold=30,
                    tip="Envia mas encuestas de satisfaccion. Los clientes que responden tienden a ser tus mejores promotores.",
                ))

        # 4. Assemble DTO
        now = dt_cls.now(tz.utc)

        result = EvangelizationDetailDTO(
            header_kpis=EvangelizationHeaderKpisDTO(**data["header_kpis"]),
            mini_funnel=MiniFunnelDTO(**data["mini_funnel"]),
            referidos=[EvangelistDTO(**e) for e in data.get("referidos", [])],
            candidatos=[CandidatoDTO(**c) for c in data.get("candidatos", [])],
            nps_summary=NpsSummaryDTO(**data["nps_summary"]),
            ugc_count=data.get("ugc_count", 0),
            ugc_written=data.get("ugc_written", 0),
            ugc_audio=data.get("ugc_audio", 0),
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 5. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "evangelization",
                "last_30_days",
                result.model_dump(),
            )

        return result

    # ------------------------------------------------------------------
    # Bowtie Summary — lightweight endpoint for the funnel row
    # ------------------------------------------------------------------

    async def get_bowtie_summary(self, tenant_id: UUID) -> BowtiesSummaryDTO:
        """Return lightweight KPIs for all 8 stages.

        Strategy: read each stage's existing Redis cache and extract only the
        2-3 KPI fields needed. Falls back to minimal DB queries on cache miss.
        The assembled summary is itself cached with a 60s TTL.
        """
        tid = str(tenant_id)

        # 1. Try summary-level cache first
        if self.cache is not None:
            cached = await self.cache.get(tid, "summary", "last_30_days")
            if cached is not None:
                return BowtiesSummaryDTO(**cached)

        stages: list[StageSummaryKpiDTO] = []
        latest_updated: Optional[str] = None

        # Helper to read a stage cache
        async def _get_stage_cache(stage: str) -> Optional[dict]:
            if self.cache is None:
                return None
            return await self.cache.get(tid, stage, "last_30_days")

        # --- Attraction ---
        attraction_cache = await _get_stage_cache("attraction")
        if attraction_cache:
            total_visitors = 0
            for group_key in ("organic_social", "ga4_search", "paid", "outbound"):
                group = attraction_cache.get(group_key, {})
                totals = group.get("totals", {})
                total_visitors += totals.get("reach", 0) + totals.get("sessions", 0) + totals.get("contacts", 0)
            connected_count = sum(
                len(attraction_cache.get(g, {}).get("channels", []))
                for g in ("organic_social", "ga4_search", "paid", "outbound")
            )
            stages.append(StageSummaryKpiDTO(
                stage="attraction", main_kpi=total_visitors,
                main_label="visitantes", secondary_kpi=connected_count,
                secondary_label="canales activos",
            ))
            if attraction_cache.get("last_updated"):
                latest_updated = attraction_cache["last_updated"]
        else:
            # Fallback: lightweight query
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
            total_visitors = int(self.db.execute(visitor_stmt).scalar() or 0)
            stages.append(StageSummaryKpiDTO(
                stage="attraction", main_kpi=total_visitors,
                main_label="visitantes", secondary_kpi=0,
                secondary_label="canales activos",
            ))

        # --- Capture ---
        capture_cache = await _get_stage_cache("capture")
        if capture_cache:
            hk = capture_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="capture", main_kpi=hk.get("total_leads", 0),
                main_label="leads", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="tasa conversion", secondary_unit="%",
            ))
        else:
            total_leads = self.lead_repo.count_total(tenant_id)
            stages.append(StageSummaryKpiDTO(
                stage="capture", main_kpi=total_leads,
                main_label="leads", secondary_kpi=0,
                secondary_label="tasa conversion", secondary_unit="%",
            ))

        # --- Nurture ---
        nurture_cache = await _get_stage_cache("nurture")
        if nurture_cache:
            hk = nurture_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="nurture", main_kpi=hk.get("total_mqls", 0),
                main_label="MQLs", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="engagement rate", secondary_unit="%",
            ))
        else:
            mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
            stages.append(StageSummaryKpiDTO(
                stage="nurture", main_kpi=mql_count,
                main_label="MQLs", secondary_kpi=0,
                secondary_label="engagement rate", secondary_unit="%",
            ))

        # --- Opportunity ---
        opportunity_cache = await _get_stage_cache("opportunity")
        if opportunity_cache:
            hk = opportunity_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="opportunity", main_kpi=hk.get("total_sqls", 0),
                main_label="SQLs", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="pipeline value", secondary_unit="%",
            ))
        else:
            sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
            opp_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.OPPORTUNITY)
            stages.append(StageSummaryKpiDTO(
                stage="opportunity", main_kpi=sql_count + opp_count,
                main_label="SQLs", secondary_kpi=0,
                secondary_label="pipeline value", secondary_unit="%",
            ))

        # --- Sales ---
        sales_cache = await _get_stage_cache("sales")
        if sales_cache:
            hk = sales_cache.get("header_kpis", {})
            mf = sales_cache.get("mini_funnel", {})
            main_val = hk.get("total_revenue", 0)
            conv_rate = mf.get("conversion_rate", 0)
            new_cust = hk.get("new_customers", 0)
            secondary = conv_rate if conv_rate > 0 else new_cust
            secondary_unit = "%" if conv_rate > 0 else None
            stages.append(StageSummaryKpiDTO(
                stage="sales", main_kpi=main_val,
                main_label="revenue", main_unit="$",
                secondary_kpi=secondary,
                secondary_label="conversion" if conv_rate > 0 else "clientes nuevos",
                secondary_unit=secondary_unit,
            ))
        else:
            from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
                SalesMetricsRepository,
            )
            from datetime import datetime as dt_cls, timedelta as td, timezone as tz

            now = dt_cls.now(tz.utc)
            start_30d = now - td(days=30)
            sales_repo = SalesMetricsRepository(self.db)
            raw_sales = sales_repo.get_sales_summary(tenant_id, start_30d, now)
            total_revenue = sum(float(r.total_revenue) for r in raw_sales)
            new_customers = sum(int(r.unique_customers) for r in raw_sales)
            stages.append(StageSummaryKpiDTO(
                stage="sales", main_kpi=total_revenue,
                main_label="revenue", main_unit="$",
                secondary_kpi=new_customers,
                secondary_label="clientes nuevos",
            ))

        # --- Adoption ---
        adoption_cache = await _get_stage_cache("adoption")
        if adoption_cache:
            hk = adoption_cache.get("header_kpis", {})
            mf = adoption_cache.get("mini_funnel", {})
            health = hk.get("health_pct", 0)
            active = hk.get("active_customers", 0)
            conv_rate = mf.get("conversion_rate", 0)
            secondary = conv_rate if conv_rate > 0 else active
            secondary_unit = "%" if conv_rate > 0 else None
            stages.append(StageSummaryKpiDTO(
                stage="adoption", main_kpi=health,
                main_label="salud %", main_unit="%",
                secondary_kpi=secondary,
                secondary_label="activacion" if conv_rate > 0 else "activos",
                secondary_unit=secondary_unit,
            ))
        else:
            stages.append(StageSummaryKpiDTO(
                stage="adoption", main_kpi=0,
                main_label="salud %", main_unit="%",
                secondary_kpi=0, secondary_label="activos",
            ))

        # --- Expansion ---
        expansion_cache = await _get_stage_cache("expansion")
        if expansion_cache:
            hk = expansion_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="expansion", main_kpi=hk.get("net_mrr", 0),
                main_label="net MRR", main_unit="$",
                secondary_kpi=hk.get("churn_rate_pct", 0),
                secondary_label="churn rate", secondary_unit="%",
            ))
        else:
            stages.append(StageSummaryKpiDTO(
                stage="expansion", main_kpi=0,
                main_label="net MRR", main_unit="$",
                secondary_kpi=0, secondary_label="churn rate", secondary_unit="%",
            ))

        # --- Evangelization ---
        evangelization_cache = await _get_stage_cache("evangelization")
        if evangelization_cache:
            hk = evangelization_cache.get("header_kpis", {})
            mf = evangelization_cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            stages.append(StageSummaryKpiDTO(
                stage="evangelization", main_kpi=hk.get("k_factor", 0),
                main_label="k-factor",
                secondary_kpi=conv_rate,
                secondary_label="conversion", secondary_unit="%" if conv_rate > 0 else None,
            ))
        else:
            evangelists = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.EVANGELIST)
            stages.append(StageSummaryKpiDTO(
                stage="evangelization", main_kpi=0,
                main_label="k-factor",
                secondary_kpi=evangelists, secondary_label="evangelistas",
            ))

        result = BowtiesSummaryDTO(
            stages=stages,
            period="last_30_days",
            last_updated=latest_updated,
        )

        # Cache the summary with short TTL
        if self.cache is not None:
            await self.cache.set(
                tid, "summary", "last_30_days", result.model_dump()
            )

        return result

    # ------------------------------------------------------------------
    # Time Series — generic daily/weekly chart data for any stage
    # ------------------------------------------------------------------

    # Suggested hex colors per channel slug (frontend may override)
    _CHANNEL_COLORS: Dict[str, str] = {
        "meta-ads": "#1877F2",
        "ig-organic": "#E4405F",
        "fb-organic": "#1877F2",
        "google-ads": "#EA4335",
        "google-organic": "#34A853",
        "yt-organic": "#FF0000",
        "yt-ads": "#FF0000",
        "tiktok-organic": "#00F2EA",
        "tiktok-ads": "#00F2EA",
        "direct": "#6B7280",
        "ai-search-organic": "#8B5CF6",
        "manychat-comments": "#0084FF",
        "linkedin-organic": "#0A66C2",
        "email-capture": "#F59E0B",
        "cold-contact": "#6B7280",
    }

    async def get_stage_timeseries(
        self,
        tenant_id: UUID,
        stage: str,
        metric_name: str = "visitors",
        range_days: int = 30,
        granularity: str = "daily",
    ) -> StageTimeSeriesDTO:
        """Return time-series data for a funnel stage, grouped by channel and date.

        Queries official_metrics WHERE tenant_id AND channel_slug IN (stage channels)
        AND metric_name = X, GROUP BY metric_date, channel_slug.
        Includes previous-period totals for delta% calculation.
        """
        from src.modules.analytics.application.services.channel_registry import (
            get_stage_channels,
        )

        tid = str(tenant_id)

        # 1. Check cache
        cache_period = f"ts:{metric_name}:{range_days}:{granularity}"
        if self.cache is not None:
            cached = await self.cache.get(tid, stage, cache_period)
            if cached is not None:
                return StageTimeSeriesDTO(**cached)

        # 2. Get channel slugs for this stage
        stage_channels = get_stage_channels(stage)
        slug_to_info = {
            ch["slug"]: ch for ch in stage_channels
        }
        channel_slugs = list(slug_to_info.keys())

        if not channel_slugs:
            return StageTimeSeriesDTO(
                stage=stage,
                metric_name=metric_name,
                granularity=granularity,
                range_days=range_days,
                data_points=[],
                channels_present=[],
                period_totals={},
                previous_period_totals=None,
            )

        # 3. Query current period
        from datetime import date as date_type, timedelta, timezone as tz

        now = datetime.now(tz.utc).date()
        start_date = now - timedelta(days=range_days)
        prev_start = start_date - timedelta(days=range_days)

        # Map metric aliases: frontend sends "visitors" but DB may have "sessions"
        db_metric_names = [metric_name]
        if metric_name == "visitors":
            db_metric_names = ["sessions", "users", "visitors"]
        elif metric_name == "leads":
            db_metric_names = ["leads", "new_subscribers"]

        from sqlalchemy import select as sa_select, func as sa_f
        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        M = OfficialMetricModel

        # Current period: group by date, channel_slug
        stmt = (
            sa_select(
                M.metric_date,
                M.channel_slug,
                sa_f.sum(M.value).label("total"),
            )
            .where(
                M.tenant_id == tenant_id,
                M.channel_slug.in_(channel_slugs),
                M.metric_name.in_(db_metric_names),
                M.metric_date >= start_date,
                M.metric_date <= now,
            )
            .group_by(M.metric_date, M.channel_slug)
            .order_by(M.metric_date)
        )
        rows = self.db.execute(stmt).all()

        # 4. Build data points
        from collections import OrderedDict

        date_map: Dict[date_type, Dict[str, float]] = OrderedDict()
        channels_seen: set = set()

        for row in rows:
            d = row.metric_date
            slug = row.channel_slug
            val = float(row.total)
            channels_seen.add(slug)
            if d not in date_map:
                date_map[d] = {}
            date_map[d][slug] = date_map[d].get(slug, 0) + val

        # Weekly aggregation if requested
        if granularity == "weekly" and date_map:
            weekly_map: Dict[date_type, Dict[str, float]] = OrderedDict()
            for d, ch_vals in date_map.items():
                # ISO week start (Monday)
                week_start = d - timedelta(days=d.weekday())
                if week_start not in weekly_map:
                    weekly_map[week_start] = {}
                for slug, val in ch_vals.items():
                    weekly_map[week_start][slug] = (
                        weekly_map[week_start].get(slug, 0) + val
                    )
            date_map = weekly_map

        data_points = [
            TimeSeriesPointDTO(
                date=d.isoformat(),
                channels=ch_vals,
            )
            for d, ch_vals in date_map.items()
        ]

        # 5. Period totals
        period_totals: Dict[str, float] = {}
        for ch_vals in date_map.values():
            for slug, val in ch_vals.items():
                period_totals[slug] = period_totals.get(slug, 0) + val

        # 6. Previous period totals
        prev_stmt = (
            sa_select(
                M.channel_slug,
                sa_f.sum(M.value).label("total"),
            )
            .where(
                M.tenant_id == tenant_id,
                M.channel_slug.in_(channel_slugs),
                M.metric_name.in_(db_metric_names),
                M.metric_date >= prev_start,
                M.metric_date < start_date,
            )
            .group_by(M.channel_slug)
        )
        prev_rows = self.db.execute(prev_stmt).all()
        previous_period_totals = {
            row.channel_slug: float(row.total) for row in prev_rows
        } if prev_rows else None

        # 7. Build channels_present
        channels_present = []
        for slug in sorted(channels_seen):
            info = slug_to_info.get(slug, {})
            channels_present.append(ChannelInfoDTO(
                slug=slug,
                name=info.get("name", slug),
                color=self._CHANNEL_COLORS.get(slug, "#6B7280"),
            ))

        result = StageTimeSeriesDTO(
            stage=stage,
            metric_name=metric_name,
            granularity=granularity,
            range_days=range_days,
            data_points=data_points,
            channels_present=channels_present,
            period_totals=period_totals,
            previous_period_totals=previous_period_totals,
        )

        # 8. Cache (5 min)
        if self.cache is not None:
            await self.cache.set(tid, stage, cache_period, result.model_dump())

        return result
