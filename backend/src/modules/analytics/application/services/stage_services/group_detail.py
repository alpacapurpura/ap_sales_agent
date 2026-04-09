"""Group Detail service — extracts a single group from cached stage data.

Tier 2 progressive loading: provides full metrics for one channel group
without requiring the full stage detail computation.

Cache strategy:
  1. Check group-specific cache: metrics:{tenant_id}:group_{stage}_{group_key}:{period}
  2. On miss, read the full stage cache (already computed by detail endpoints)
  3. Extract the requested group's channels and totals
  4. Cache the group detail with 5-min TTL
"""

import structlog

from src.modules.analytics.application.dto.attraction_dto import (
    ChannelMetricDTO,
    MetricValueDTO,
)
from src.modules.analytics.application.dto.group_detail_dto import GroupDetailDTO
from src.modules.analytics.application.services.stage_services.constants import (
    STAGE_GROUPS as _STAGE_GROUPS,
)
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache

logger = structlog.get_logger()

GROUP_DETAIL_TTL = 300  # 5 minutes


class GroupDetailService:
    """Provides detail data for a single channel group within a stage."""

    def __init__(self, cache: MetricsCache | None = None):
        self.cache = cache

    async def get_group_detail(
        self, tenant_id: str, stage: str, group_key: str, period: str
    ) -> GroupDetailDTO:
        """Return full detail for a single group within a stage.

        Strategy:
        1. Check group-specific cache
        2. On miss, read the full stage cache
        3. Extract the requested group
        4. Cache the result
        """
        # 1. Check group-specific cache
        group_cache_key = f"group_{stage}_{group_key}"
        if self.cache is not None:
            cached = await self.cache.get(tenant_id, group_cache_key, period)
            if cached is not None:
                logger.debug(
                    "group_detail_cache_hit",
                    tenant_id=tenant_id,
                    stage=stage,
                    group_key=group_key,
                )
                return GroupDetailDTO(**cached)

        # 2. Read full stage cache
        stage_data: dict | None = None
        if self.cache is not None:
            stage_data = await self.cache.get(tenant_id, stage, period)

        # 3. Extract group
        extracted = self._extract_group(stage, stage_data, group_key)

        if extracted is None:
            return GroupDetailDTO(
                group_key=group_key,
                stage=stage,
                channels=[],
                totals={},
                period=period,
            )

        dto = GroupDetailDTO(
            group_key=extracted["group_key"],
            stage=stage,
            channels=[self._map_channel(ch) for ch in extracted["channels"]],
            totals=extracted["totals"],
            period=stage_data.get("period", period) if stage_data else period,
        )

        # 4. Cache the result
        if self.cache is not None:
            await self.cache.set(tenant_id, group_cache_key, period, dto.model_dump())

        logger.info(
            "group_detail_computed",
            tenant_id=tenant_id,
            stage=stage,
            group_key=group_key,
            channels=len(dto.channels),
        )
        return dto

    def _extract_group(
        self, stage: str, stage_data: dict | None, group_key: str
    ) -> dict | None:
        """Extract a single group's data from the full stage cache."""
        if stage_data is None:
            return None

        stage_groups = _STAGE_GROUPS.get(stage, [])
        for gk, _label, field_name in stage_groups:
            if gk == group_key:
                group_data = stage_data.get(field_name)
                if group_data is None or not isinstance(group_data, dict):
                    return None
                return {
                    "group_key": group_key,
                    "channels": group_data.get("channels", []),
                    "totals": group_data.get("totals", {}),
                }

        return None

    @staticmethod
    def _map_channel(ch: dict) -> ChannelMetricDTO:
        """Map a raw channel dict from cache to ChannelMetricDTO."""
        metrics = []
        for m in ch.get("metrics", []):
            if isinstance(m, dict):
                metrics.append(
                    MetricValueDTO(
                        name=m.get("name", ""),
                        value=float(m.get("value", 0)),
                        unit=m.get("unit", "count"),
                        currency=m.get("currency"),
                        breakdown=m.get("breakdown"),
                    )
                )

        return ChannelMetricDTO(
            slug=ch.get("slug", ""),
            name=ch.get("name", ""),
            channel_type=ch.get("channel_type", ""),
            metrics=metrics,
            source_label=ch.get("source_label", ""),
            connected=ch.get("connected", False),
            cost_type=ch.get("cost_type"),
            last_updated=ch.get("last_updated"),
            stale=ch.get("stale", False),
            error_message=ch.get("error_message"),
            provider_name=ch.get("provider_name"),
        )
