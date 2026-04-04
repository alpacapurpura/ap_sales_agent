"""MetricsService -- thin facade for marketing funnel visualization.

Delegates stage-specific logic to dedicated service classes in
stage_services/. Keeps only the sankey endpoint (legacy) and
orchestration/delegation code.

Stage services:
- AttractionStageService   -> get_attraction_metrics()
- CaptureStageService      -> get_capture_metrics()
- NurtureStageService       -> get_nurturing_metrics()
- OpportunityStageService  -> get_opportunity_metrics()
- SalesStageService         -> get_sales_metrics()
- AdoptionStageService     -> get_adoption_metrics()
- ExpansionStageService    -> get_expansion_metrics()
- EvangelizationStageService -> get_evangelization_metrics()
- SummaryStageService      -> get_bowtie_summary()
- TimeseriesStageService   -> get_stage_timeseries()
"""

from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional

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
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO
from src.modules.analytics.application.dto.capture_dto import CaptureDetailDTO
from src.modules.analytics.application.dto.nurture_dto import NurtureDetailDTO
from src.modules.analytics.application.dto.opportunity_dto import OpportunityDetailDTO
from src.modules.analytics.application.dto.adoption_dto import AdoptionDetailDTO
from src.modules.analytics.application.dto.sales_dto import SalesDetailDTO
from src.modules.analytics.application.dto.expansion_dto import ExpansionDetailDTO
from src.modules.analytics.application.dto.evangelization_dto import EvangelizationDetailDTO
from src.modules.analytics.application.dto.summary_dto import BowtiesSummaryDTO
from src.modules.analytics.application.dto.timeseries_dto import StageTimeSeriesDTO
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.application.services.stage_services import (
    AdoptionStageService,
    AttractionStageService,
    CaptureStageService,
    EvangelizationStageService,
    ExpansionStageService,
    NurtureStageService,
    OpportunityStageService,
    SalesStageService,
    SummaryStageService,
    TimeseriesStageService,
)

# Maps our channel slugs to the ChannelType enum for connection lookups (sankey legacy)
_CHANNEL_CONNECTION_MAP: Dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,
    "yt-ads": ChannelType.YOUTUBE,
}


class MetricsService:
    """Facade that provides dashboard metrics for marketing funnel stages.

    Delegates stage-specific logic to dedicated service classes.
    Keeps only the sankey endpoint (legacy) and delegation code.

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

        # Stage services
        self._attraction = AttractionStageService(db, cache, connection_port)
        self._capture = CaptureStageService(db, cache, connection_port)
        self._nurture = NurtureStageService(db, cache, connection_port)
        self._opportunity = OpportunityStageService(db, cache, connection_port)
        self._sales = SalesStageService(db, cache, connection_port, offer_port)
        self._adoption = AdoptionStageService(db, cache, connection_port, offer_port)
        self._expansion = ExpansionStageService(db, cache, connection_port, offer_port)
        self._evangelization = EvangelizationStageService(
            db, cache, connection_port, offer_port
        )
        self._summary = SummaryStageService(db, cache, connection_port, offer_port)
        self._timeseries = TimeseriesStageService(db, cache, connection_port)

    # ------------------------------------------------------------------
    # Sankey (legacy — stays in MetricsService)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Stage delegations — public API preserved
    # ------------------------------------------------------------------

    async def get_attraction_metrics(
        self, tenant_id: UUID, period: str = "last_30_days"
    ) -> AttractionDetailDTO:
        return await self._attraction.get_metrics(tenant_id, period)

    async def get_capture_metrics(
        self, tenant_id: UUID, period: str = "last_30_days"
    ) -> CaptureDetailDTO:
        return await self._capture.get_metrics(tenant_id, period)

    async def get_nurturing_metrics(
        self, tenant_id: UUID, period: str = "last_30_days"
    ) -> NurtureDetailDTO:
        return await self._nurture.get_metrics(tenant_id, period)

    async def get_opportunity_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> OpportunityDetailDTO:
        return await self._opportunity.get_metrics(tenant_id, start_date, end_date)

    async def get_sales_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> SalesDetailDTO:
        return await self._sales.get_metrics(tenant_id, start_date, end_date)

    async def get_adoption_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> AdoptionDetailDTO:
        return await self._adoption.get_metrics(tenant_id, start_date, end_date)

    async def get_expansion_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> ExpansionDetailDTO:
        return await self._expansion.get_metrics(tenant_id, start_date, end_date)

    async def get_evangelization_metrics(
        self,
        tenant_id: UUID,
        start_date: "datetime",
        end_date: "datetime",
    ) -> EvangelizationDetailDTO:
        return await self._evangelization.get_metrics(tenant_id, start_date, end_date)

    async def get_bowtie_summary(self, tenant_id: UUID) -> BowtiesSummaryDTO:
        return await self._summary.get_summary(tenant_id)

    async def get_stage_timeseries(
        self,
        tenant_id: UUID,
        stage: str,
        metric_name: str = "visitors",
        range_days: int = 30,
        granularity: str = "daily",
    ) -> StageTimeSeriesDTO:
        return await self._timeseries.get_timeseries(
            tenant_id, stage, metric_name, range_days, granularity
        )
