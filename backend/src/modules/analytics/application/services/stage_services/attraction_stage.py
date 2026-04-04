"""Attraction stage service — extracted from MetricsService.

Handles get_attraction_metrics() logic: ETL official tables,
ChannelRegistry, grouping into organic_social/ga4_search/paid/outbound/website.
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.services.aggregation_helpers import (
    compute_channel_totals,
)
from src.modules.analytics.application.services.channel_registry import ChannelRegistry
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)

# Channel types -> group mapping for the 5-group structure
_GROUP_MAP: Dict[str, str] = {
    "social": "organic_social",
    "search": "ga4_search",
    "direct": "ga4_search",
    "paid": "paid",
    "outbound": "outbound",
    "website": "website",
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


class AttractionStageService:
    """Provides attraction stage metrics for the Bowtie dashboard."""

    def __init__(
        self,
        db: Session,
        cache: Optional[MetricsCache] = None,
        connection_port: Optional[ConnectionPort] = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

    @staticmethod
    def _classify_error(error_text: Optional[str]) -> Optional[str]:
        """Map extraction error to a user-facing message."""
        if not error_text:
            return None
        error_lower = error_text.lower()
        for key, msg in _ERROR_MESSAGES.items():
            if key in error_lower:
                return msg
        return "Servicio no disponible"

    async def get_metrics(
        self, tenant_id: UUID, period: str = "last_30_days"
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
        agg_by_slug: Dict[str, list] = defaultdict(list)
        for agg in aggregations:
            agg_by_slug[agg.channel_slug].append(agg)

        # 4. Get extraction run status for stale detection
        from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
            ExtractionRunRepository,
        )
        run_repo = ExtractionRunRepository(self.db)

        # Build provider -> latest run lookup (deduplicate per provider)
        provider_runs: Dict[str, object] = {}

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
                    elif latest_run.status == "partial_success":
                        failures = latest_run.sub_extractor_failures or []
                        if failures:
                            names = [
                                f["extractor_name"].replace("_", " ").title()
                                for f in failures[:2]
                            ]
                            error_message = f"Parcial ({', '.join(names)})"

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
