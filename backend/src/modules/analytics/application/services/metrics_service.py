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
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.modules.analytics.application.services.channel_registry import (
    ChannelRegistry,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.domain.ports import ConnectionPort

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
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

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
