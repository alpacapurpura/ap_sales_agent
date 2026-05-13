"""Group Detail DTO for Tier 2 progressive loading.

Returns data for a single channel group within a stage,
providing the full metrics for that group's channels only.
Much lighter than the full stage detail (~50-100 fields vs ~500+).
"""

from luana_core_analytics_engine.application.dto.attraction_dto import ChannelMetricDTO
from pydantic import BaseModel, ConfigDict


class GroupDetailDTO(BaseModel):
    """Response for a single group's detail within a stage."""

    model_config = ConfigDict(from_attributes=True)

    group_key: str
    stage: str
    channels: list[ChannelMetricDTO]
    totals: dict[str, float]
    period: str = "last_30_days"
