"""Attraction stage service — extracted from MetricsService.

Handles get_attraction_metrics() logic: ETL official tables,
ChannelRegistry, grouping into organic_social/ga4_search/paid/outbound.
"""

from collections import defaultdict
from datetime import date
from uuid import UUID

from luana_core_analytics_engine.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)
from luana_core_analytics_engine.application.services.aggregation_helpers import (
    compute_channel_totals,
)
from luana_core_analytics_engine.application.services.channel_registry import ChannelRegistry
from luana_core_analytics_engine.application.services.stage_services.constants import (
    ATTRACTION_GROUP_MAP as _GROUP_MAP,
)
from luana_core_analytics_engine.application.services.stage_services.constants import (
    DISPLAY_NAME_MAP as _DISPLAY_NAME_MAP,
)
from luana_core_analytics_engine.application.services.stage_services.constants import (
    ERROR_MESSAGES as _ERROR_MESSAGES,
)
from luana_core_analytics_engine.domain.period_config import DateRange
from luana_core_analytics_engine.domain.ports import ConnectionPort
from luana_core_analytics_engine.infrastructure.cache.metrics_cache import MetricsCache
from luana_core_analytics_engine.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from sqlalchemy.orm import Session


def _enrich_with_derived_metrics(
    metrics: list[MetricValueDTO],
    channel_slug: str,
    repo: OfficialMetricsRepository,
    tenant_id: UUID,
    provider_name: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[MetricValueDTO]:
    """Compute DERIVED and NON_AGGREGABLE metrics missing from aggregations.

    - DERIVED (cpc, cpm): calculated from components already in metrics.
    - NON_AGGREGABLE (reach): fetched from last 30 days of official_metrics.
    """
    existing = {m.name: m.value for m in metrics}

    # ── DERIVED metrics: cpc = spend / clicks, cpm = spend / impressions x 1000
    spend = existing.get("spend")
    if spend and spend > 0:
        clicks = existing.get("clicks")
        if clicks and clicks > 0 and "cpc" not in existing:
            metrics.append(
                MetricValueDTO(
                    name="cpc",
                    value=round(spend / clicks, 2),
                    unit="currency",
                    currency=next(
                        (m.currency for m in metrics if m.name == "spend"),
                        None,
                    ),
                ),
            )
        impressions = existing.get("impressions")
        if impressions and impressions > 0 and "cpm" not in existing:
            metrics.append(
                MetricValueDTO(
                    name="cpm",
                    value=round(spend / impressions * 1000, 2),
                    unit="currency",
                    currency=next(
                        (m.currency for m in metrics if m.name == "spend"),
                        None,
                    ),
                ),
            )

    # ── NON_AGGREGABLE metrics: reach (last available value from official_metrics)
    if "reach" not in existing and provider_name and start_date and end_date:
        raw = repo.get_channel_metrics(
            tenant_id,
            provider_name,
            channel_slug,
            start_date,
            end_date,
        )
        reach_val = raw.get("reach")
        if isinstance(reach_val, (int, float)) and reach_val > 0:
            metrics.append(MetricValueDTO(name="reach", value=float(reach_val)))

    return metrics


class AttractionStageService:
    """Provides attraction stage metrics for the Bowtie dashboard."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
    ) -> None:
        """Initialize attraction stage service."""
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

    @staticmethod
    def _classify_error(error_text: str | None) -> str | None:
        """Map extraction error to a user-facing message."""
        if not error_text:
            return None
        error_lower = error_text.lower()
        for key, msg in _ERROR_MESSAGES.items():
            if key in error_lower:
                return msg
        return "Servicio no disponible"

    def _build_agg_metrics(
        self,
        agg_rows: list,
    ) -> tuple[list[MetricValueDTO], str | None]:
        """Build MetricValueDTO list from aggregation rows, returning latest timestamp."""
        metrics: list[MetricValueDTO] = []
        last_updated: str | None = None

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

            if hasattr(agg, "computed_at") and agg.computed_at:
                ts = agg.computed_at.isoformat()
                if last_updated is None or ts > last_updated:
                    last_updated = ts

        return metrics, last_updated

    def _detect_stale_status(
        self,
        provider_name: str,
        tenant_id: UUID,
        provider_runs: dict[str, object],
        run_repo: "object",
    ) -> tuple[bool, str | None]:
        """Check extraction run status and return (stale, error_message)."""
        if not provider_name or provider_name in ("internal", "manual"):
            return False, None

        if provider_name not in provider_runs:
            provider_runs[provider_name] = run_repo.get_latest(tenant_id, provider_name)
        latest_run = provider_runs[provider_name]
        if not latest_run:
            return False, None

        if latest_run.status in ("failed", "retrying"):
            return True, self._classify_error(latest_run.error)

        if latest_run.status == "partial_success":
            failures = latest_run.sub_extractor_failures or []
            if failures:
                names = [f["extractor_name"].replace("_", " ").title() for f in failures[:2]]
                return False, f"Parcial ({', '.join(names)})"

        return False, None

    async def get_metrics(
        self,
        tenant_id: UUID,
        date_range: DateRange,
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
            cached = await self.cache.get(str(tenant_id), "attraction", date_range.period_type)
            if cached is not None:
                return AttractionDetailDTO(**cached)

        # 2. Get dynamic channel list from ChannelRegistry
        registry = ChannelRegistry(self.connection_port)
        channel_split = await registry.get_available_channels(tenant_id, "attraction")

        # 3. Get aggregated metrics from official tables
        repo = OfficialMetricsRepository(self.db)
        aggregations = repo.get_channel_summary(tenant_id, "attraction", date_range.period_type)

        agg_by_slug: dict[str, list] = defaultdict(list)
        for agg in aggregations:
            agg_by_slug[agg.channel_slug].append(agg)

        # 4. Get extraction run status for stale detection
        from luana_core_analytics_engine.infrastructure.repositories.extraction_run_repository import (
            ExtractionRunRepository,
        )

        run_repo = ExtractionRunRepository(self.db)
        provider_runs: dict[str, object] = {}

        # 5. Build ChannelMetricDTO lists grouped by section
        groups: dict[str, list[ChannelMetricDTO]] = {
            "organic_social": [],
            "ga4_search": [],
            "paid": [],
            "outbound": [],
        }
        available_channels: list[ChannelMetricDTO] = []
        latest_updated: str | None = None

        for ch in channel_split.get("connected", []):
            slug = ch["slug"]
            channel_type = ch["channel_type"]
            group_key = _GROUP_MAP.get(channel_type, "organic_social")
            provider_name = ch.get("provider_name", "")

            # Build metrics from aggregation rows
            agg_rows = agg_by_slug.get(slug, [])
            metrics, last_updated = self._build_agg_metrics(agg_rows)
            if last_updated and (latest_updated is None or last_updated > latest_updated):
                latest_updated = last_updated

            # Stale detection
            stale, error_message = self._detect_stale_status(
                provider_name,
                tenant_id,
                provider_runs,
                run_repo,
            )

            # For ManyChat channels, read from official_metrics directly
            if provider_name == "manychat":
                mc_metrics = OfficialMetricsRepository(self.db).get_channel_metrics(
                    tenant_id,
                    "manychat",
                    slug,
                    date_range.start_date,
                    date_range.end_date,
                )
                existing_names = {m.name for m in metrics}
                for m_name, m_value in mc_metrics.items():
                    if m_name not in existing_names:
                        metrics.append(
                            MetricValueDTO(name=m_name, value=float(m_value)),
                        )

            # Enrich with DERIVED and NON_AGGREGABLE metrics
            metrics = _enrich_with_derived_metrics(
                metrics,
                slug,
                repo,
                tenant_id,
                provider_name,
                start_date=date_range.start_date,
                end_date=date_range.end_date,
            )

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

        # 6. Compute group totals
        available_dto = AvailableChannelsDTO(channels=available_channels) if available_channels else None

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
            available=available_dto,
            period=date_range.period_type,
            last_updated=latest_updated,
        )

        # 7. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "attraction",
                date_range.period_type,
                result.model_dump(),
            )

        return result
