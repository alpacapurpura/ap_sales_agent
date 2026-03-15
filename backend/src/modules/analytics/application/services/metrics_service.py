from uuid import UUID
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.modules.crm.infrastructure.repositories.customer_repository import JourneyEventRepository, CustomerRepository
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import LeadRepository
from src.modules.crm.domain.enums import LifecycleStage
from src.modules.connections.infrastructure.repositories.channel_connection_repository import ChannelConnectionRepository
from src.modules.connections.domain.enums import ChannelType
from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    TrafficGroupDTO,
    ChannelMetricDTO,
)

# Maps our channel slugs to the ChannelType enum for connection lookups
_CHANNEL_CONNECTION_MAP: Dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,  # closest available
    "yt-ads": ChannelType.YOUTUBE,
}


class MetricsService:
    def __init__(self, db: Session):
        self.journey_repo = JourneyEventRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)
        self.connection_repo = ChannelConnectionRepository(db)

    def get_marketing_sankey_metrics(self, tenant_id: UUID) -> Dict[str, Any]:
        """
        Obtiene métricas para el diagrama de Sankey de marketing (7 nodos).
        
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
        opp_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.OPPORTUNITY)
        opportunities = sql_count + opp_count
        
        # 5. Customers (Conversion)
        customers = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.CUSTOMER)
        
        # 6. Loyal Customers (Retention)
        # Placeholder heuristic: 40% of customers are retained/loyal
        retention = int(customers * 0.4)
        
        # 7. Evangelists (Advocacy)
        evangelists = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.EVANGELIST)
        
        # Ensure logical flow consistency for visualization (optional but good for Sankey)
        # We won't force-clamp to avoid hiding data issues, but we'll use these values for links.

        nodes = [
            {"name": "Adquisition"},
            {"name": "Activation"},
            {"name": "Consideration"},
            {"name": "Decision"},
            {"name": "Conversion"},
            {"name": "Retention"},
            {"name": "Advocacy"}
        ]
        
        links = [
            {"source": 0, "target": 1, "value": leads},
            {"source": 1, "target": 2, "value": qualified},
            {"source": 2, "target": 3, "value": opportunities},
            {"source": 3, "target": 4, "value": customers},
            {"source": 4, "target": 5, "value": retention},
            {"source": 5, "target": 6, "value": evangelists}
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
                "evangelists": evangelists
            }
        }

    def _is_connected(self, tenant_id: UUID, slug: str) -> bool:
        """Check if a channel has an active connection for this tenant."""
        channel_type = _CHANNEL_CONNECTION_MAP.get(slug)
        if not channel_type:
            return False
        conn = self.connection_repo.get_active(tenant_id, channel_type)
        return conn is not None

    def get_attraction_metrics(self, tenant_id: UUID) -> AttractionDetailDTO:
        """
        Returns attraction-stage metrics: 13 channels split into organic and paid groups.

        For v1, visitor counts come from journey_events (unique visitors grouped by source).
        Channels without real data return 0.
        Connection status is checked against channel_connections.
        """
        # Get real visitor counts grouped by source from journey events
        visitors = self.journey_repo.get_unique_visitors(tenant_id)

        # Define all channels with their metadata
        organic_channels_def = [
            ("ig-organic", "Instagram", "ORGANIC_SOCIAL", "Instagram Graph API"),
            ("yt-organic", "YouTube", "ORGANIC_SOCIAL", "YouTube Analytics"),
            ("fb-organic", "Facebook", "ORGANIC_SOCIAL", "Facebook Page Insights"),
            ("tiktok-organic", "TikTok", "ORGANIC_SOCIAL", "TikTok Analytics"),
            ("linkedin-organic", "LinkedIn", "ORGANIC_SOCIAL", "LinkedIn Analytics"),
            ("google-organic", "Google Orgánico", "ORGANIC_SEARCH", "Google Analytics 4"),
            ("direct", "Tráfico Directo", "ORGANIC_SEARCH", "Google Analytics 4"),
            ("ai-search-organic", "AI Search", "ORGANIC_SEARCH", "Google Analytics 4"),
        ]

        paid_channels_def = [
            ("meta-ads", "Meta Ads", "PAID_MEDIA", "Meta Ads Manager"),
            ("google-ads", "Google Ads", "PAID_MEDIA", "Google Ads"),
            ("tiktok-ads", "TikTok Ads", "PAID_MEDIA", "TikTok Ads Manager"),
            ("yt-ads", "YouTube Ads", "PAID_MEDIA", "Google Ads"),
            ("cold-contact", "Contacto en Frío", "PAID_MEDIA", "Manual / CRM"),
        ]

        organic_channels: List[ChannelMetricDTO] = []
        for slug, name, ch_type, source in organic_channels_def:
            organic_channels.append(ChannelMetricDTO(
                slug=slug,
                name=name,
                channel_type=ch_type,
                value=0,  # v1: real data will come from journey_events aggregation
                source_label=source,
                connected=self._is_connected(tenant_id, slug),
            ))

        paid_channels: List[ChannelMetricDTO] = []
        for slug, name, ch_type, source in paid_channels_def:
            paid_channels.append(ChannelMetricDTO(
                slug=slug,
                name=name,
                channel_type=ch_type,
                value=0,
                cost=0,
                source_label=source,
                connected=self._is_connected(tenant_id, slug),
            ))

        organic_total = sum(ch.value for ch in organic_channels)
        paid_total = sum(ch.value for ch in paid_channels)
        paid_cost_total = sum(ch.cost or 0 for ch in paid_channels)

        return AttractionDetailDTO(
            organic=TrafficGroupDTO(
                total_value=organic_total,
                channels=organic_channels,
            ),
            paid=TrafficGroupDTO(
                total_value=paid_total,
                total_cost=paid_cost_total,
                channels=paid_channels,
            ),
            period="last_30_days",
        )
