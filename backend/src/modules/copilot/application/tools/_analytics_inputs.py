"""Pydantic v2 input schemas for analytics copilot tools.

Adversarial defense:
- Literal enums for stage/channel/period → path injection + XSS rejected at parse time
- extra='forbid' → tenant_override payload-key smuggling rejected

Mirrors frontend zod schemas in:
  frontend/src/features/growth-studio/schemas/stage-filter-params.schema.ts
  frontend/src/features/growth-studio/schemas/channel-config.schema.ts
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

# Spanish slugs matching FE STAGE_REGISTRY
StageSlug = Literal[
    "atraccion-captura",
    "nutricion-oportunidad",
    "ventas",
    "adopcion",
    "expansion-evangelizacion",
]

# Canonical channel slugs matching FE CHANNEL_REGISTRY
ChannelSlug = Literal[
    "meta-ads",
    "yt-organic",
    "email-nurture",
    "ig-organic",
    "website-total",
]

# Valid period values
StagePeriod = Literal["7d", "30d", "90d"]


class StageFilterParams(BaseModel):
    """Input schema for get_stage_metrics tool.

    extra='forbid' blocks payload-key smuggling (e.g. tenant_id override).
    Literal enums reject path injection + XSS at Pydantic parse time.
    """

    model_config = ConfigDict(extra="forbid")

    stage: StageSlug
    channel: ChannelSlug | None = None
    period: StagePeriod = "30d"


class ChannelOverviewParams(BaseModel):
    """Input schema for get_channel_overview tool.

    extra='forbid' rejects all extra fields including tenant_id override.
    """

    model_config = ConfigDict(extra="forbid")

    channel: ChannelSlug


class TriggerEtlRefreshParams(BaseModel):
    """Input schema for trigger_etl_refresh tool.

    extra='forbid' prevents tenant_id or confirmed injection beyond declared fields.
    """

    model_config = ConfigDict(extra="forbid")

    channel: ChannelSlug
    confirmed: bool = False
