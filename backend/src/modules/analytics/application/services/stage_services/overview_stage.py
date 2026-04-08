"""Stage Overview service — lightweight data for progressive loading.

Composes a StageOverviewDTO from existing stage Redis caches,
extracting only the fields needed for the overview (header KPIs,
channel list with 1 headline KPI, group summaries, bottlenecks).

Cache strategy:
  1. Check overview-specific cache: metrics:{tenant_id}:overview_{stage}:{period}
  2. On miss, read the full stage cache (already computed by detail endpoints)
  3. Extract overview fields from the cached stage data
  4. Cache the overview with 5-min TTL
"""

import structlog

from src.modules.analytics.application.dto.stage_overview_dto import (
    BottleneckOverviewDTO,
    ChannelOverviewDTO,
    GroupOverviewDTO,
    MetricValueDTO,
    MiniFunnelOverviewDTO,
    StageOverviewDTO,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache

logger = structlog.get_logger()

# Stage -> group definitions: each entry is (group_key, group_label, dto_field_name)
_STAGE_GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "attraction": [
        ("organic_social", "Social Orgánico", "organic_social"),
        ("ga4_search", "Búsqueda Orgánica", "ga4_search"),
        ("paid", "Pagado", "paid"),
        ("outbound", "Outbound", "outbound"),
    ],
    "capture": [
        ("web_infrastructure", "Web / Infraestructura", "web_infrastructure"),
        ("ai_agent", "AI Agent / Mensajería", "ai_agent"),
    ],
    "nurture": [
        ("retargeting", "Retargeting", "retargeting"),
        ("automation", "Automatización", "automation"),
    ],
    "opportunity": [
        ("checkout", "Checkout", "checkout"),
        ("payment_links", "Links de Pago", "payment_links"),
        ("qualification", "Calificación", "qualification"),
    ],
    "sales": [
        ("adquisicion", "Adquisición", "adquisicion"),
        ("expansion", "Expansión", "expansion"),
    ],
    "adoption": [],  # No channel groups -- uses offers list
    "expansion": [
        ("retencion", "Retención", "retencion"),
        ("crecimiento", "Crecimiento", "crecimiento"),
        ("cancelaciones", "Cancelaciones", "cancelaciones"),
    ],
    "evangelization": [],  # No channel groups -- uses referidos, candidatos
}

# Stage -> header KPI keys to extract from the cached stage data
_STAGE_HEADER_KPI_KEYS: dict[str, list[str]] = {
    "attraction": ["reach", "sessions", "impressions"],
    "capture": ["total_leads", "conversion_rate", "cost_per_lead"],
    "nurture": ["total_mqls", "conversion_rate", "cost_per_mql"],
    "opportunity": ["total_sqls", "conversion_rate", "cost_per_sql"],
    "sales": ["total_revenue", "new_customers", "cac"],
    "adoption": ["active_customers", "inactive_customers", "health_pct"],
    "expansion": ["net_mrr", "avg_ltv", "churn_rate_pct"],
    "evangelization": ["k_factor", "referral_conversions", "nps_score"],
}

# Stage -> headline KPI metric name for channels (first metric found wins)
_HEADLINE_KPI_PRIORITY: dict[str, list[str]] = {
    "attraction": ["reach", "impressions", "sessions", "clicks", "views"],
    "capture": ["leads", "new_subscribers", "conversations"],
    "nurture": ["mqls", "retargeting_reach", "email_opens"],
    "opportunity": ["checkouts", "meetings_booked", "payment_links_sent"],
    "sales": ["total_revenue", "sales_count"],
    "adoption": ["active_count", "health_pct"],
    "expansion": ["revenue", "total_revenue"],
    "evangelization": ["referrals_sent", "conversions"],
}

OVERVIEW_TTL = 300  # 5 minutes


class StageOverviewService:
    """Provides lightweight stage overview data for progressive loading."""

    def __init__(self, cache: MetricsCache | None = None):
        self.cache = cache

    async def get_stage_overview(
        self, tenant_id: str, stage: str, period: str
    ) -> StageOverviewDTO:
        """Return a lightweight overview for a funnel stage.

        Strategy:
        1. Check overview-specific cache
        2. On miss, read the full stage cache
        3. Extract overview fields
        4. Cache the overview
        """
        # 1. Check overview cache
        if self.cache is not None:
            overview_key = f"overview_{stage}"
            cached = await self.cache.get(tenant_id, overview_key, period)
            if cached is not None:
                logger.debug(
                    "stage_overview_cache_hit",
                    tenant_id=tenant_id,
                    stage=stage,
                    period=period,
                )
                return StageOverviewDTO(**cached)

        # 2. Read full stage cache
        stage_data: dict | None = None
        if self.cache is not None:
            stage_data = await self.cache.get(tenant_id, stage, period)

        # 3. Extract overview from stage data
        overview = self._extract_overview(stage, stage_data)

        # 4. Cache the overview (skip empty overviews to avoid cache poisoning)
        if self.cache is not None and (overview.channel_list or overview.groups):
            overview_key = f"overview_{stage}"
            await self.cache.set(tenant_id, overview_key, period, overview.model_dump())

        logger.info(
            "stage_overview_computed",
            tenant_id=tenant_id,
            stage=stage,
            period=period,
            channels=len(overview.channel_list),
            groups=len(overview.groups),
        )
        return overview

    def _extract_overview(
        self, stage: str, stage_data: dict | None
    ) -> StageOverviewDTO:
        """Extract overview fields from full stage cached data."""
        if stage_data is None:
            return self._empty_overview(stage)

        header_kpis = self._extract_header_kpis(stage, stage_data)
        mini_funnel = self._extract_mini_funnel(stage_data)
        groups = self._extract_groups(stage, stage_data)
        channel_list = self._extract_channel_list(stage, stage_data)
        bottlenecks = self._extract_bottlenecks(stage_data)

        return StageOverviewDTO(
            stage=stage,
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            groups=groups,
            channel_list=channel_list,
            bottlenecks=bottlenecks,
            period=stage_data.get("period", "last_30_days"),
            last_updated=stage_data.get("last_updated"),
        )

    def _empty_overview(self, stage: str) -> StageOverviewDTO:
        """Return an empty overview when no cached data exists."""
        return StageOverviewDTO(
            stage=stage,
            header_kpis={},
            groups=[],
            channel_list=[],
            bottlenecks=[],
        )

    def _extract_header_kpis(self, stage: str, data: dict) -> dict[str, float | None]:
        """Extract header KPIs from cached stage data."""
        kpis: dict[str, float | None] = {}
        header_data = data.get("header_kpis", {})

        # For attraction, header KPIs come from group totals
        if stage == "attraction":
            total_reach = 0.0
            total_sessions = 0.0
            total_impressions = 0.0
            for group_key in ("organic_social", "ga4_search", "paid", "outbound"):
                group = data.get(group_key, {})
                totals = group.get("totals", {}) if isinstance(group, dict) else {}
                total_reach += totals.get("reach", 0)
                total_sessions += totals.get("sessions", 0)
                total_impressions += totals.get("impressions", 0)
            kpis["total_reach"] = total_reach
            kpis["total_sessions"] = total_sessions
            kpis["total_impressions"] = total_impressions
        else:
            # Most stages have a header_kpis dict
            kpi_keys = _STAGE_HEADER_KPI_KEYS.get(stage, [])
            for key in kpi_keys:
                val = header_data.get(key)
                if val is not None:
                    kpis[key] = float(val) if isinstance(val, (int, float)) else None
                else:
                    kpis[key] = None

        return kpis

    def _extract_mini_funnel(self, data: dict) -> MiniFunnelOverviewDTO | None:
        """Extract mini-funnel data if present."""
        mf = data.get("mini_funnel")
        if not mf or not isinstance(mf, dict):
            return None

        return MiniFunnelOverviewDTO(
            source_label=mf.get("source_label", ""),
            source_value=float(mf.get("source_value", 0)),
            target_label=mf.get("target_label", ""),
            target_value=float(mf.get("target_value", 0)),
            conversion_rate=float(mf.get("conversion_rate", 0)),
        )

    def _extract_groups(self, stage: str, data: dict) -> list[GroupOverviewDTO]:
        """Extract group summaries from cached stage data."""
        groups: list[GroupOverviewDTO] = []
        stage_groups = _STAGE_GROUPS.get(stage, [])

        for group_key, group_label, field_name in stage_groups:
            group_data = data.get(field_name)
            if group_data is None:
                continue

            if isinstance(group_data, dict):
                channels = group_data.get("channels", [])
                channel_count = len(channels) if isinstance(channels, list) else 0
            else:
                channel_count = 0

            groups.append(
                GroupOverviewDTO(
                    group_key=group_key,
                    group_label=group_label,
                    channel_count=channel_count,
                )
            )

        return groups

    def _extract_channel_list(self, stage: str, data: dict) -> list[ChannelOverviewDTO]:
        """Extract lightweight channel list from cached stage data."""
        channels: list[ChannelOverviewDTO] = []
        stage_groups = _STAGE_GROUPS.get(stage, [])
        headline_priority = _HEADLINE_KPI_PRIORITY.get(stage, [])

        for group_key, _label, field_name in stage_groups:
            group_data = data.get(field_name)
            if not group_data or not isinstance(group_data, dict):
                continue

            group_channels = group_data.get("channels", [])
            if not isinstance(group_channels, list):
                continue

            for ch in group_channels:
                if not isinstance(ch, dict):
                    continue
                headline_kpi = self._pick_headline_kpi(ch, headline_priority)
                channels.append(
                    ChannelOverviewDTO(
                        slug=ch.get("slug", ""),
                        name=ch.get("name", ""),
                        channel_type=ch.get("channel_type", ""),
                        group_key=group_key,
                        connected=ch.get("connected", False),
                        headline_kpi=headline_kpi,
                        last_updated=ch.get("last_updated"),
                        stale=ch.get("stale", False),
                        provider_name=ch.get("provider_name"),
                    )
                )

        return channels

    @staticmethod
    def _pick_headline_kpi(channel: dict, priority: list[str]) -> MetricValueDTO | None:
        """Pick the first matching headline KPI from a channel's metrics."""
        metrics = channel.get("metrics", [])
        if not isinstance(metrics, list):
            return None

        metrics_by_name: dict[str, dict] = {}
        for m in metrics:
            if isinstance(m, dict) and "name" in m:
                metrics_by_name[m["name"]] = m

        for kpi_name in priority:
            if kpi_name in metrics_by_name:
                m = metrics_by_name[kpi_name]
                return MetricValueDTO(
                    name=m["name"],
                    value=float(m.get("value", 0)),
                    unit=m.get("unit"),
                )

        # Fallback: use first metric
        if metrics and isinstance(metrics[0], dict):
            m = metrics[0]
            return MetricValueDTO(
                name=m.get("name", ""),
                value=float(m.get("value", 0)),
                unit=m.get("unit"),
            )

        return None

    def _extract_bottlenecks(self, data: dict) -> list[BottleneckOverviewDTO]:
        """Extract bottleneck alerts if present."""
        raw = data.get("bottlenecks", [])
        if not isinstance(raw, list):
            return []

        result: list[BottleneckOverviewDTO] = []
        for b in raw:
            if isinstance(b, dict):
                result.append(
                    BottleneckOverviewDTO(
                        type=b.get("type", ""),
                        metric_label=b.get("metric_label", ""),
                        severity=b.get("severity", "normal"),
                    )
                )
        return result
