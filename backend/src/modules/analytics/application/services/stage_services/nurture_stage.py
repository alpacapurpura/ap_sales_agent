"""Nurture stage service — extracted from MetricsService.

Handles get_nurturing_metrics() logic: MQL counts, costs,
retargeting/automation grouping, mini funnel (Leads -> MQLs).
"""

from collections import defaultdict
from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.attraction_dto import (
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.nurture_dto import (
    NurtureDetailDTO,
    NurtureHeaderKpisDTO,
)
from src.modules.analytics.application.services.aggregation_helpers import (
    compute_channel_totals,
)
from src.modules.analytics.application.services.channel_registry import ChannelRegistry
from src.modules.analytics.application.services.stage_cost_service import (
    StageCostService,
)
from src.modules.analytics.application.services.stage_services.constants import (
    DISPLAY_NAME_MAP as _DISPLAY_NAME_MAP,
)
from src.modules.analytics.application.services.stage_services.constants import (
    NURTURE_GROUP_MAP as _NURTURE_GROUP_MAP,
)
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.repositories.nurture_repository import (
    NurtureMetricsRepository,
)
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)


class NurtureStageService:
    """Provides nurture stage metrics for the Bowtie dashboard."""

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
    def _build_email_nurture_metrics(
        email_events: dict[str, int],
    ) -> list[MetricValueDTO]:
        """Build metrics for the email-nurture channel from CRM events."""
        emails_sent = email_events.get("emails_sent", 0)
        opens = email_events.get("opens", 0)
        clicks = email_events.get("clicks", 0)
        open_rate = round(opens / emails_sent * 100, 2) if emails_sent > 0 else 0.0
        click_rate = round(clicks / emails_sent * 100, 2) if emails_sent > 0 else 0.0
        return [
            MetricValueDTO(name="emails_sent", value=float(emails_sent)),
            MetricValueDTO(name="open_rate", value=open_rate, unit="percentage"),
            MetricValueDTO(name="click_rate", value=click_rate, unit="percentage"),
        ]

    @staticmethod
    def _build_ai_sdr_metrics(
        followup_events: dict[str, int],
    ) -> list[MetricValueDTO]:
        """Build metrics for the ai-sdr channel from CRM followup events."""
        sent = followup_events.get("sent", 0)
        replied = followup_events.get("replied", 0)
        response_rate = round(replied / sent * 100, 2) if sent > 0 else 0.0
        return [
            MetricValueDTO(name="followups", value=float(sent)),
            MetricValueDTO(
                name="response_rate",
                value=response_rate,
                unit="percentage",
            ),
        ]

    @staticmethod
    def _build_retargeting_metrics(agg_rows: list) -> list[MetricValueDTO]:
        """Build metrics for retargeting channels from ETL aggregation rows."""
        metrics: list[MetricValueDTO] = []
        for agg in agg_rows:
            extra_data = getattr(agg, "extra", None) or {}
            breakdown = extra_data if isinstance(extra_data, dict) and extra_data else None
            metrics.append(
                MetricValueDTO(
                    name=agg.metric_name,
                    value=agg.value,
                    unit=agg.unit or "count",
                    currency=getattr(agg, "currency", None),
                    breakdown=breakdown,
                ),
            )
        return metrics

    def _load_nurture_costs(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
        total_mqls: int,
    ) -> tuple[float, float | None, float | None]:
        """Load nurture costs and return (cost_per_mql, retargeting_cpm, automation_cpm)."""
        cost_svc = StageCostService(self.db)
        manual_costs = cost_svc.get_channel_costs(tenant_id, "nurture")
        retargeting_spend = cost_svc.get_retargeting_spend(
            tenant_id,
            start_date,
            end_date,
        )
        all_costs = {**manual_costs, **retargeting_spend}
        total_cost = sum(all_costs.values())
        cost_per_mql = cost_svc.calculate_cost_per_mql(total_cost, total_mqls)
        retargeting_cpm = cost_svc.get_group_cost_per_mql(
            "retargeting",
            tenant_id,
            start_date,
            end_date,
            total_mqls,
        )
        automation_cpm = cost_svc.get_group_cost_per_mql(
            "automation",
            tenant_id,
            start_date,
            end_date,
            total_mqls,
        )
        return cost_per_mql, retargeting_cpm, automation_cpm

    def _supplement_manychat(
        self,
        metrics: list[MetricValueDTO],
        tenant_id: UUID,
        slug: str,
        start_date: "object",
        end_date: "object",
    ) -> None:
        """Append ManyChat metrics from official_metrics (in-place)."""
        mc_metrics = OfficialMetricsRepository(self.db).get_channel_metrics(
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

    async def get_metrics(
        self,
        tenant_id: UUID,
        period: str = "last_30_days",
    ) -> NurtureDetailDTO:
        """Return nurture-stage (Stage 2) metrics."""
        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "nurture", "last_30_days")
            if cached is not None:
                return NurtureDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(tenant_id, "nurture")

        # 3. Get aggregated metrics from official tables
        repo = OfficialMetricsRepository(self.db)
        aggregations = repo.get_channel_summary(tenant_id, "nurture", "last_30_days")

        agg_by_slug: dict[str, list] = defaultdict(list)
        for agg in aggregations:
            agg_by_slug[agg.channel_slug].append(agg)

        # 4. Query CRM for MQL counts
        from datetime import datetime, timedelta

        now = datetime.now(UTC)
        start_date = now - timedelta(days=30)

        nurture_repo = NurtureMetricsRepository(self.db)
        total_mqls = nurture_repo.count_new_mqls(tenant_id, start_date, now)
        total_leads = nurture_repo.count_leads_in_period(tenant_id, start_date, now)

        # 5. Load costs
        cost_per_mql, retargeting_cpm, automation_cpm = self._load_nurture_costs(
            tenant_id,
            start_date,
            now,
            total_mqls,
        )

        # 6. Query CRM for internal channel-specific data
        email_events = nurture_repo.count_email_events(tenant_id, start_date, now)
        followup_events = nurture_repo.count_followup_events(tenant_id, start_date, now)

        slug_metrics_dispatch: dict[str, list[MetricValueDTO]] = {
            "email-nurture": self._build_email_nurture_metrics(email_events),
            "ai-sdr": self._build_ai_sdr_metrics(followup_events),
        }

        # 7. Build ChannelMetricDTO lists grouped by section
        groups: dict[str, list[ChannelMetricDTO]] = {
            "retargeting": [],
            "automation": [],
        }
        available_channels: list[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            provider_name = ch.get("provider_name", "")
            group_key = _NURTURE_GROUP_MAP.get(ch["channel_type"], "automation")

            metrics = slug_metrics_dispatch.get(slug)
            if metrics is None:
                metrics = self._build_retargeting_metrics(agg_by_slug.get(slug, []))

            if provider_name == "manychat":
                self._supplement_manychat(
                    metrics,
                    tenant_id,
                    slug,
                    start_date,
                    now,
                )

            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = conn_config.get(display_name_key) if display_name_key else None

            groups[group_key].append(
                ChannelMetricDTO(
                    slug=slug,
                    name=ch["name"],
                    channel_type=ch["channel_type"],
                    metrics=metrics,
                    source_label=ch["source_label"],
                    connected=True,
                    source_display_name=source_display,
                    provider_name=provider_name,
                ),
            )

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
        ]

        # 8. Compute group totals
        retargeting_totals = compute_channel_totals(groups["retargeting"])
        if retargeting_cpm is not None:
            retargeting_totals["cost_per_mql"] = retargeting_cpm
        automation_totals = compute_channel_totals(groups["automation"])
        if automation_cpm is not None:
            automation_totals["cost_per_mql"] = automation_cpm

        conversion_rate = round(total_mqls / total_leads * 100, 2) if total_leads > 0 else 0.0
        available_dto = AvailableChannelsDTO(channels=available_channels) if available_channels else None

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

        # 9. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "nurture",
                "last_30_days",
                result.model_dump(),
            )

        return result
