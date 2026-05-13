"""SegmentFilter DSL — v1 predefined fields.

Minimal v1 + extensible-ready abstract base.
Arch test enforces extra='forbid' on all *SegmentFilter* classes.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal

from luana_core_campaigns.domain.enums import SegmentFilterCombinator
from pydantic import BaseModel, ConfigDict, Field

# v1 catalog — predefined fields only (covers 100% of FOUNDATION segment catalog).
# vNext = ExpressiveSegmentFilter (full JSON-logic DSL) — out of scope post PI-1.

LifecycleStage = Literal["VISITOR", "SUBSCRIBER", "MQL", "SQL", "CUSTOMER", "CHURNED"]
LeadTemperature = Literal["COLD", "WARM", "HOT"]
ChannelIdentifier = Literal["telegram_id", "whatsapp_id", "instagram_id", "tiktok_id", "email"]


class ScoreRange(BaseModel):
    """Score range filter for fit_score and intent_score."""

    model_config = ConfigDict(extra="forbid")

    fit_score_min: int | None = Field(default=None, ge=0, le=100)
    fit_score_max: int | None = Field(default=None, ge=0, le=100)
    intent_score_min: int | None = Field(default=None, ge=0, le=100)
    intent_score_max: int | None = Field(default=None, ge=0, le=100)


class DateRange(BaseModel):
    """UTC date range filter (gte/lte)."""

    model_config = ConfigDict(extra="forbid")

    gte: dt.datetime | None = None  # UTC
    lte: dt.datetime | None = None


class TagsFilter(BaseModel):
    """Tag-based filter with any/all mode."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["any", "all"] = "any"
    tags: list[str] = Field(default_factory=list)


class PredefinedSegmentFilter(BaseModel):
    """v1 catalog of predefined segment filter fields.

    extra='forbid' enforced by arch test (test_segment_filter_pydantic_validated.py).

    Combinator logic: combinator='all' => AND, 'any' => OR (top-level only).
    Nested groups (mixed AND/OR) NOT supported v1; tracked as decisiones diferidas.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    combinator: SegmentFilterCombinator = SegmentFilterCombinator.ALL

    lifecycle_stage: list[LifecycleStage] | None = None
    temperature: list[LeadTemperature] | None = None
    score_range: ScoreRange | None = None
    source: list[str] | None = None  # UTM source / channel_type
    country: list[str] | None = Field(default=None)  # ISO 3166-1 alpha-2 lowercase, e.g. ["pe", "mx"]
    created_at_range: DateRange | None = None
    last_interaction_at_range: DateRange | None = None
    tags: TagsFilter | None = None
    is_blacklisted: bool | None = None
    has_channel_id: list[ChannelIdentifier] | None = None


# Type alias used by Segment.filter_dsl.
# Future: Union[PredefinedSegmentFilter, ExpressiveSegmentFilter].
SegmentFilter = PredefinedSegmentFilter
