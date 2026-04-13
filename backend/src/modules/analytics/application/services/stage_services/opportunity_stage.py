"""Opportunity stage service — extracted from MetricsService.

Handles get_opportunity_metrics() logic: SQL pipeline counts,
checkout/meeting/payment_link events, bottleneck detection.
"""

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
from src.modules.analytics.application.dto.opportunity_dto import (
    BottleneckDTO,
    OpportunityDetailDTO,
    OpportunityHeaderKpisDTO,
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
    OPPORTUNITY_GROUP_MAP as _OPPORTUNITY_GROUP_MAP,
)
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)


class OpportunityStageService:
    """Provides opportunity stage metrics for the Bowtie dashboard."""

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
    def _build_slug_metrics(
        slug: str,
        checkout_events: dict,
        meeting_events: dict,
        payment_link_events: dict,
    ) -> list[MetricValueDTO]:
        """Build metrics list for a specific opportunity channel slug."""
        checkout_count = checkout_events["checkout_initiated"]["count"]

        slug_dispatch: dict[str, list[MetricValueDTO]] = {
            "checkout-init": [
                MetricValueDTO(name="count", value=float(checkout_count)),
                MetricValueDTO(
                    name="value",
                    value=checkout_events["checkout_initiated"]["value"],
                    unit="currency",
                    currency="USD",
                ),
            ],
            "link-enviado": [
                MetricValueDTO(name="count", value=float(payment_link_events["count"])),
                MetricValueDTO(
                    name="value",
                    value=payment_link_events["value"],
                    unit="currency",
                    currency="USD",
                ),
            ],
            "checkout-lp": [
                MetricValueDTO(name="count", value=0.0),
                MetricValueDTO(
                    name="value",
                    value=0.0,
                    unit="currency",
                    currency="USD",
                ),
            ],
            "meeting-booked": [
                MetricValueDTO(name="booked", value=float(meeting_events["booked"])),
                MetricValueDTO(
                    name="completed",
                    value=float(meeting_events["completed"]),
                ),
                MetricValueDTO(name="no_show", value=float(meeting_events["no_show"])),
                MetricValueDTO(
                    name="rescheduled",
                    value=float(meeting_events["rescheduled"]),
                ),
            ],
        }

        if slug == "abandoned-cart":
            abandoned_count = checkout_events["cart_abandoned"]["count"]
            abandonment_rate = (
                round(abandoned_count / checkout_count * 100, 2)
                if checkout_count > 0
                else 0.0
            )
            return [
                MetricValueDTO(name="count", value=float(abandoned_count)),
                MetricValueDTO(
                    name="value",
                    value=checkout_events["cart_abandoned"]["value"],
                    unit="currency",
                    currency="USD",
                ),
                MetricValueDTO(
                    name="abandonment_rate",
                    value=abandonment_rate,
                    unit="percentage",
                ),
            ]

        return slug_dispatch.get(slug, [])

    @staticmethod
    def _detect_opportunity_bottlenecks(
        checkout_events: dict,
        meeting_events: dict,
    ) -> list[BottleneckDTO]:
        """Detect abandoned cart and no-show bottlenecks."""
        bottlenecks: list[BottleneckDTO] = []
        checkout_count = checkout_events["checkout_initiated"]["count"]
        abandoned_count = checkout_events["cart_abandoned"]["count"]

        if checkout_count > 0:
            abandon_rate = (abandoned_count / checkout_count) * 100
            if abandon_rate > 30:
                severity = "critical" if abandon_rate > 50 else "warning"
                threshold = 50.0 if abandon_rate > 50 else 30.0
                bottlenecks.append(
                    BottleneckDTO(
                        type="abandoned_cart",
                        metric_label="Tasa de Abandono",
                        current_rate=round(abandon_rate, 1),
                        severity=severity,
                        threshold=threshold,
                        tip="Revisa tu proceso de pago y considera email de recuperacion de carrito",
                    ),
                )

        meeting_booked = meeting_events["booked"]
        meeting_no_show = meeting_events["no_show"]
        if meeting_booked > 0:
            no_show_rate = (meeting_no_show / meeting_booked) * 100
            if no_show_rate > 20:
                severity = "critical" if no_show_rate > 40 else "warning"
                threshold = 40.0 if no_show_rate > 40 else 20.0
                bottlenecks.append(
                    BottleneckDTO(
                        type="meeting_no_show",
                        metric_label="Tasa de No-Show",
                        current_rate=round(no_show_rate, 1),
                        severity=severity,
                        threshold=threshold,
                        tip="Considera recordatorios automaticos antes de la reunion",
                    ),
                )

        return bottlenecks

    async def get_metrics(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> OpportunityDetailDTO:
        """Return opportunity-stage (Stage 3) metrics."""
        from datetime import datetime as dt_cls

        from src.modules.analytics.infrastructure.repositories.opportunity_repository import (
            OpportunityMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "opportunity", "last_30_days")
            if cached is not None:
                return OpportunityDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(tenant_id, "opportunity")

        # 3. Query CRM for SQL pipeline metrics
        repo = OpportunityMetricsRepository(self.db)
        total_sqls = repo.count_new_sqls(tenant_id, start_date, end_date)
        mql_count = repo.count_mqls_in_period(tenant_id, start_date, end_date)
        checkout_events = repo.count_checkout_events(tenant_id, start_date, end_date)
        meeting_events = repo.count_meeting_events(tenant_id, start_date, end_date)
        payment_link_events = repo.count_payment_link_events(
            tenant_id,
            start_date,
            end_date,
        )

        # 4. Calculate header KPIs
        conversion_rate = (
            round(total_sqls / mql_count * 100, 2) if mql_count > 0 else 0.0
        )
        cost_svc = StageCostService(self.db)
        total_cost = sum(cost_svc.get_channel_costs(tenant_id, "opportunity").values())
        cost_per_sql = cost_svc.calculate_cost_per_mql(total_cost, total_sqls)

        # 5. Build channel groups
        groups: dict[str, list[ChannelMetricDTO]] = {
            "checkout": [],
            "payment_links": [],
            "qualification": [],
        }
        available_channels: list[ChannelMetricDTO] = []

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            group_key = _OPPORTUNITY_GROUP_MAP.get(ch["channel_type"], "checkout")
            provider_name = ch.get("provider_name", "")

            metrics = self._build_slug_metrics(
                slug,
                checkout_events,
                meeting_events,
                payment_link_events,
            )

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
                        metrics.append(
                            MetricValueDTO(name=m_name, value=float(m_value)),
                        )

            conn_config = ch.get("connection_config", {})
            display_name_key = _DISPLAY_NAME_MAP.get(provider_name, "")
            source_display = (
                conn_config.get(display_name_key) if display_name_key else None
            )

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

        # 6. Bottleneck detection
        bottlenecks = self._detect_opportunity_bottlenecks(
            checkout_events,
            meeting_events,
        )

        available_dto = (
            AvailableChannelsDTO(channels=available_channels)
            if available_channels
            else None
        )
        now = dt_cls.now(UTC)

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

        # 7. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "opportunity",
                "last_30_days",
                result.model_dump(),
            )

        return result
