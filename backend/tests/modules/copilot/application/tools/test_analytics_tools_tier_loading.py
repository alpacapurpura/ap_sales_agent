"""TDD — Tier loading / truncation tests for get_stage_metrics. Written RED first.

Tests:
- tier_used field present in response
- truncated=True set when channel_breakdown > _CHANNEL_BREAKDOWN_LIMIT (10)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

_GET_TENANT_ID = "luana_core_copilot.application.tools.analytics_tools.get_tenant_id"
_CALL_STAGE_OV = "luana_core_copilot.application.tools.analytics_tools._call_stage_overview"


def _make_stage_overview(**kwargs) -> MagicMock:
    """Create a MagicMock mimicking StageOverviewDTO."""
    m = MagicMock()
    m.stage = kwargs.get("stage", "attraction")
    m.period = kwargs.get("period", "last_30_days")
    m.header_kpis = kwargs.get("header_kpis", [])
    m.channels = kwargs.get("channels", [])
    m.groups = kwargs.get("groups", [])
    return m


class TestTierUsedField:
    """tier_used field always present in get_stage_metrics response."""

    def test_tier_used_present_in_response(self) -> None:
        """Response always includes tier_used field."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert "tier_used" in parsed
        # Tier 1 = overview, should be 1
        assert parsed["tier_used"] in (0, 1, 2, 3)

    def test_tier_used_is_1_for_overview_response(self) -> None:
        """When calling overview (Tier 1), tier_used should be 1."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert parsed["tier_used"] == 1


class TestTruncationFlag:
    """truncated flag is set when channel_breakdown exceeds _CHANNEL_BREAKDOWN_LIMIT (10)."""

    def test_truncated_false_by_default(self) -> None:
        """With 0 channels, truncated=False."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert "truncated" in parsed
        assert parsed["truncated"] is False

    def test_truncated_true_when_many_channels(self) -> None:
        """When channels list is > 10, truncated=True and breakdown is capped."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        # Simulate many channels (> _CHANNEL_BREAKDOWN_LIMIT=10)
        mock_channel = MagicMock()
        mock_channel.slug = "test-channel"
        mock_channel.name = "Test"
        mock_channel.headline_kpi = None

        overview = _make_stage_overview(channels=[mock_channel] * 15)  # 15 channels

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert "truncated" in parsed
        assert parsed["truncated"] is True
        # Also verify channel_breakdown is capped at 10
        assert len(parsed.get("channel_breakdown", [])) <= 10


class TestStageMetricsResponseShape:
    """Verify all required fields are present in response."""

    def test_response_has_all_required_fields(self) -> None:
        """All required fields present in successful response."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview(stage="adoption")

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "adopcion"})

        parsed = json.loads(result)
        required_fields = ["stage_name", "period", "kpis", "tier_used", "truncated"]
        for field in required_fields:
            assert field in parsed, f"Missing required field: {field}"
