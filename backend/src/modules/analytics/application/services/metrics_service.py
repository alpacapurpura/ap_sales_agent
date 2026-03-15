"""MetricsService — dashboard data for marketing funnel visualization.

get_attraction_metrics() reads from ETL official tables via:
- MetricsCache (5-min Redis TTL)
- OfficialMetricsRepository / MetricAggregationModel
- ChannelRegistry (dynamic channel list from ConnectionPort)

get_marketing_sankey_metrics() still reads from journey_events (separate migration).
"""

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

# Channel types classified as paid (for grouping into TrafficGroupDTOs)
_PAID_CHANNEL_TYPES = {"paid", "outbound"}


class MetricsService:
    """Provides dashboard metrics for marketing funnel stages.

    Constructor accepts optional cache and connection_port for backward
    compatibility — the sankey endpoint doesn't need them.
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

    async def get_attraction_metrics(
        self, tenant_id: UUID
    ) -> AttractionDetailDTO:
        """Return attraction-stage metrics from ETL official tables.

        Flow:
        1. Check MetricsCache (5-min TTL)
        2. On miss: ChannelRegistry -> OfficialMetricsRepository -> build DTOs
        3. Cache result before returning

        Channels with no data return value=0.
        Unconnected channels go to the 'available' section.
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

        # Build lookup: channel_slug -> aggregation row
        agg_by_slug: Dict[str, Any] = {}
        for agg in aggregations:
            agg_by_slug[agg.channel_slug] = agg

        # 4. Build ChannelMetricDTO lists
        organic_channels: List[ChannelMetricDTO] = []
        paid_channels: List[ChannelMetricDTO] = []
        available_channels: List[ChannelMetricDTO] = []

        latest_updated: Optional[str] = None

        # Connected channels
        for ch in channel_split.get("connected", []):
            agg = agg_by_slug.get(ch["slug"])
            value = agg.value if agg else 0.0
            cost_type = agg.cost_type if agg else None
            unit = agg.unit if agg else "count"
            currency = agg.currency if agg else None
            last_updated = None
            if agg and hasattr(agg, "computed_at") and agg.computed_at:
                last_updated = agg.computed_at.isoformat()
                if latest_updated is None or last_updated > latest_updated:
                    latest_updated = last_updated

            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                value=value,
                cost=agg.value if agg and ch["channel_type"] in _PAID_CHANNEL_TYPES else None,
                source_label=ch["source_label"],
                connected=True,
                cost_type=cost_type,
                unit=unit,
                currency=currency,
                last_updated=last_updated,
            )

            if ch["channel_type"] in _PAID_CHANNEL_TYPES:
                paid_channels.append(dto)
            else:
                organic_channels.append(dto)

        # Available (unconnected) channels
        for ch in channel_split.get("available", []):
            dto = ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                value=0.0,
                source_label=ch["source_label"],
                connected=False,
                cost_type=None,
                unit="count",
            )
            available_channels.append(dto)

        # 5. Build result
        organic_total = sum(ch.value for ch in organic_channels)
        paid_total = sum(ch.value for ch in paid_channels)
        paid_cost_total = sum(ch.cost or 0 for ch in paid_channels)

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )

        result = AttractionDetailDTO(
            organic=TrafficGroupDTO(
                total_value=organic_total,
                channels=organic_channels,
            ),
            paid=TrafficGroupDTO(
                total_value=paid_total,
                total_cost=paid_cost_total,
                channels=paid_channels,
            ),
            available=available_dto,
            period="last_30_days",
            last_updated=latest_updated,
        )

        # 6. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "attraction",
                "last_30_days",
                result.model_dump(),
            )

        return result
