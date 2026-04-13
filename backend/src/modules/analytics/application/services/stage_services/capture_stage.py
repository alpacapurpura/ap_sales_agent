"""Capture stage service — extracted from MetricsService.

Handles get_capture_metrics() logic: CRM lead counts, costs,
grouping into web_infrastructure and ai_agent.
"""

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    SubSourceDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import (
    CaptureDetailDTO,
    CaptureHeaderKpisDTO,
    MiniFunnelDTO,
)
from src.modules.analytics.application.services.aggregation_helpers import (
    compute_channel_totals,
)
from src.modules.analytics.application.services.capture_cost_service import (
    CaptureCostService,
)
from src.modules.analytics.application.services.channel_registry import ChannelRegistry
from src.modules.analytics.application.services.stage_services.constants import (
    CAPTURE_GROUP_MAP as _CAPTURE_GROUP_MAP,
)
from src.modules.analytics.application.services.stage_services.constants import (
    DISPLAY_NAME_MAP as _DISPLAY_NAME_MAP,
)
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.repositories.capture_repository import (
    CaptureMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)


class CaptureStageService:
    """Provides capture stage metrics for the Bowtie dashboard."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

    @staticmethod
    def _merge_manychat_into_meta(
        channels: list[ChannelMetricDTO],
        detailed_leads: dict[str, int],
        conversation_counts: dict[str, int],
    ) -> None:
        """Merge manychat-ig into ig-dm as a unified card (in-place).

        When both ig-dm and manychat-ig exist in the channel list, the
        manychat-ig card is removed and the ig-dm card gets sub_sources
        showing the per-source breakdown.
        """
        merge_pairs = [
            ("ig-dm", "manychat-ig"),
            ("whatsapp-inbound", "manychat-wa"),
        ]

        for meta_slug, mc_slug in merge_pairs:
            meta_dto = next((c for c in channels if c.slug == meta_slug), None)
            mc_dto = next((c for c in channels if c.slug == mc_slug), None)

            if not meta_dto or not mc_dto:
                continue

            meta_leads = detailed_leads.get(meta_slug, 0)
            mc_leads = detailed_leads.get(mc_slug, 0)
            meta_convs = conversation_counts.get(meta_slug, 0)
            mc_convs = conversation_counts.get(mc_slug, 0)

            meta_dto.sub_sources = [
                SubSourceDTO(
                    name="Meta Direct",
                    leads=meta_leads,
                    conversations=meta_convs,
                ),
                SubSourceDTO(name="ManyChat", leads=mc_leads, conversations=mc_convs),
            ]

            existing_names = {m.name for m in meta_dto.metrics}
            for m in mc_dto.metrics:
                if m.name not in existing_names:
                    meta_dto.metrics.append(m)

            channels.remove(mc_dto)

    def _build_website_capture_dto(
        self,
        ch: dict,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> ChannelMetricDTO:
        """Build the website-capture channel DTO from GA4 + Meta data."""
        official_repo = OfficialMetricsRepository(self.db)
        sd = start_date.date() if hasattr(start_date, "date") else start_date
        ed = end_date.date() if hasattr(end_date, "date") else end_date

        ga4_organic = official_repo.get_channel_metrics(
            tenant_id,
            "google_analytics",
            "google-organic",
            sd,
            ed,
        )
        ga4_ai = official_repo.get_channel_metrics(
            tenant_id,
            "google_analytics",
            "ai-search-organic",
            sd,
            ed,
        )
        ga4_direct = official_repo.get_channel_metrics(
            tenant_id,
            "google_analytics",
            "direct",
            sd,
            ed,
        )
        ga4_total = official_repo.get_channel_metrics(
            tenant_id,
            "google_analytics",
            "website-total",
            sd,
            ed,
        )
        meta_ads = official_repo.get_channel_metrics(
            tenant_id,
            "meta",
            "meta-ads",
            sd,
            ed,
        )

        seo = ga4_organic.get("sessions", 0)
        ai_search = ga4_ai.get("sessions", 0)
        direct = ga4_direct.get("sessions", 0)
        campaign_visitors = meta_ads.get("meta_landing_page_views", 0)
        total = ga4_total.get("sessions", 0)

        if total == 0:
            total = seo + ai_search + direct + campaign_visitors

        wc_metrics = [
            MetricValueDTO(
                name="visitors",
                value=float(total),
                breakdown={
                    "campaigns": float(campaign_visitors),
                    "seo": float(seo),
                    "ai_search": float(ai_search),
                    "direct": float(direct),
                },
            ),
        ]

        return ChannelMetricDTO(
            slug=ch["slug"],
            name=ch["name"],
            channel_type=ch["channel_type"],
            metrics=wc_metrics,
            source_label=ch["source_label"],
            connected=total > 0 or campaign_visitors > 0,
            provider_name="internal",
        )

    def _supplement_manychat_metrics(
        self,
        metrics: list[MetricValueDTO],
        tenant_id: UUID,
        slug: str,
        start_date: "object",
        end_date: "object",
    ) -> None:
        """Append ManyChat-specific metrics from official_metrics (in-place)."""
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

    def _supplement_mailerlite_metrics(
        self,
        metrics: list[MetricValueDTO],
        lead_count: int,
        tenant_id: UUID,
        slug: str,
        start_date: "object",
        end_date: "object",
    ) -> list[MetricValueDTO]:
        """Append MailerLite metrics; substitute leads from new_subscribers if needed."""
        official_repo = OfficialMetricsRepository(self.db)
        ml_metrics = official_repo.get_channel_metrics(
            tenant_id,
            "mailerlite",
            slug,
            start_date.date() if hasattr(start_date, "date") else start_date,
            end_date.date() if hasattr(end_date, "date") else end_date,
        )
        existing_names = {m.name for m in metrics}
        ns = ml_metrics.get("new_subscribers", 0)
        if lead_count == 0 and ns > 0:
            metrics = [m for m in metrics if m.name != "leads"]
            metrics.insert(0, MetricValueDTO(name="leads", value=float(ns)))
        for m_name, m_value in ml_metrics.items():
            if m_name not in existing_names and m_name != "new_subscribers":
                metrics.append(MetricValueDTO(name=m_name, value=float(m_value)))
        return metrics

    def _get_merged_costs(
        self,
        tenant_id: UUID,
        connected_slugs: list[str],
    ) -> tuple["CaptureCostService", dict[str, float]]:
        """Load channel + prorated agency costs, return service and merged dict."""
        cost_service = CaptureCostService(self.db)
        channel_costs = cost_service.get_channel_costs(tenant_id)
        prorated_costs = cost_service.get_prorated_agency_costs(
            tenant_id,
            connected_slugs,
        )
        all_costs: dict[str, float] = {}
        for slug, amount in channel_costs.items():
            all_costs[slug] = all_costs.get(slug, 0.0) + amount
        for slug, amount in prorated_costs.items():
            all_costs[slug] = all_costs.get(slug, 0.0) + amount
        return cost_service, all_costs

    def _get_stage0_visitors(self, tenant_id: UUID) -> int:
        """Query aggregated visitor total (reach + sessions) for attraction stage."""
        from sqlalchemy import func as sa_func
        from sqlalchemy import select

        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        visitor_stmt = select(
            sa_func.coalesce(sa_func.sum(MetricAggregationModel.value), 0.0),
        ).where(
            MetricAggregationModel.tenant_id == tenant_id,
            MetricAggregationModel.metric_name.in_(("reach", "sessions")),
            MetricAggregationModel.period_type == "last_30_days",
        )
        return int(self.db.execute(visitor_stmt).scalar() or 0)

    def _build_capture_channel_dto(
        self,
        ch: dict,
        tenant_id: UUID,
        lead_counts: dict[str, int],
        conversation_counts: dict[str, int],
        all_costs: dict[str, float],
        stage0_visitors: int,
        start_date: "object",
        end_date: "object",
    ) -> ChannelMetricDTO:
        """Build a single capture ChannelMetricDTO for a non-website channel."""
        slug = ch["slug"]
        channel_type = ch["channel_type"]
        lead_count = lead_counts.get(slug, 0)
        channel_cost = all_costs.get(slug, 0.0)
        conv_count = conversation_counts.get(slug, 0)
        conv_rate = round(lead_count / stage0_visitors * 100, 2) if stage0_visitors > 0 else 0.0

        metrics: list[MetricValueDTO] = [
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

        if channel_type == "messaging":
            metrics.append(
                MetricValueDTO(name="conversations", value=float(conv_count)),
            )

        provider_name = ch.get("provider_name", "")
        if provider_name == "manychat":
            self._supplement_manychat_metrics(
                metrics,
                tenant_id,
                slug,
                start_date,
                end_date,
            )
        elif provider_name == "email_marketing":
            metrics = self._supplement_mailerlite_metrics(
                metrics,
                lead_count,
                tenant_id,
                slug,
                start_date,
                end_date,
            )

        conn_config = ch.get("connection_config", {})
        display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
        source_display = conn_config.get(display_name_key) if display_name_key else None

        return ChannelMetricDTO(
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

    async def get_metrics(
        self,
        tenant_id: UUID,
        period: str = "last_30_days",
    ) -> CaptureDetailDTO:
        """Return capture-stage (Stage 1) metrics."""
        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "capture", "last_30_days")
            if cached is not None:
                return CaptureDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(tenant_id, "capture")

        # 3. Query CRM for lead counts by lead_source
        from datetime import datetime, timedelta

        now = datetime.now(UTC)
        start_date = now - timedelta(days=30)
        end_date = now

        capture_repo = CaptureMetricsRepository(self.db)
        lead_counts = capture_repo.count_leads_by_source(
            tenant_id,
            start_date,
            end_date,
        )
        conversation_counts = capture_repo.count_conversations_by_channel(
            tenant_id,
            start_date,
            end_date,
        )

        # 4. Get costs
        connected_slugs = [ch["slug"] for ch in channel_split.get("connected", [])]
        cost_service, all_costs = self._get_merged_costs(tenant_id, connected_slugs)

        # 5. Get Stage 0 visitor total
        stage0_visitors = self._get_stage0_visitors(tenant_id)

        # 6. Build ChannelMetricDTO lists grouped by section
        groups: dict[str, list[ChannelMetricDTO]] = {
            "web_infrastructure": [],
            "ai_agent": [],
        }
        available_channels: list[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            group_key = _CAPTURE_GROUP_MAP.get(ch["channel_type"], "web_infrastructure")

            if slug == "website-capture":
                groups["web_infrastructure"].append(
                    self._build_website_capture_dto(
                        ch,
                        tenant_id,
                        start_date,
                        end_date,
                    ),
                )
                continue

            dto = self._build_capture_channel_dto(
                ch,
                tenant_id,
                lead_counts,
                conversation_counts,
                all_costs,
                stage0_visitors,
                start_date,
                end_date,
            )
            groups[group_key].append(dto)

        # Merge manychat-ig into ig-dm as a unified card with sub_sources
        detailed_leads = capture_repo.count_leads_by_source_detailed(
            tenant_id,
            start_date,
            end_date,
        )
        self._merge_manychat_into_meta(
            groups["ai_agent"],
            detailed_leads,
            conversation_counts,
        )

        # Available (unconnected) channels -- remove manychat-ig/wa if merged
        merged_slugs = {"manychat-ig", "manychat-wa"}
        available_channels = [
            ChannelMetricDTO(
                slug=ch["slug"],
                name=ch["name"],
                channel_type=ch["channel_type"],
                metrics=[],
                source_label=ch["source_label"],
                connected=False,
            )
            for ch in channel_split.get("available", [])
            if ch["slug"] not in merged_slugs
        ]

        # 7. Compute group totals
        total_leads = sum(lead_counts.values())
        total_costs = sum(all_costs.values())
        overall_conv_rate = round(total_leads / stage0_visitors * 100, 2) if stage0_visitors > 0 else 0.0
        cal = cost_service.calculate_cal(total_costs, total_leads)

        available_dto = AvailableChannelsDTO(channels=available_channels) if available_channels else None

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
