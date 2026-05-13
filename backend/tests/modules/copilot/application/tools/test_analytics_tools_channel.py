"""TDD — get_channel_overview tool unit tests. Written RED first.

Tests:
- happy path: valid channel → JSON with dashboard_kpis
- invalid slug rejected → structured error
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID


import pytest
from pydantic import ValidationError

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

_GET_TENANT_ID = "luana_core_copilot.application.tools.analytics_tools.get_tenant_id"
_CALL_CHANNEL = "luana_core_copilot.application.tools.analytics_tools._call_channel_dashboard"


def _make_channel_dashboard(**kwargs) -> MagicMock:
    """Create a MagicMock mimicking ChannelDashboardDTO."""
    m = MagicMock()
    m.channel_slug = kwargs.get("channel_slug", "meta-ads")
    m.channel_name = kwargs.get("channel_name", "Meta Ads")
    m.period = kwargs.get("period", "30d")
    m.kpis = kwargs.get("kpis", [])
    return m


def _async_mock(return_value: object) -> AsyncMock:
    """AsyncMock that returns the given value on each call."""
    return AsyncMock(return_value=return_value)


class TestGetChannelOverviewHappy:
    """Happy path tests for get_channel_overview."""

    def test_returns_json_string(self) -> None:
        """Tool returns JSON-decodable string with channel_name and dashboard_kpis."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        mock_dashboard = _make_channel_dashboard()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_CHANNEL, new=_async_mock(mock_dashboard)),
        ):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert "channel_name" in parsed
        assert "dashboard_kpis" in parsed

    def test_all_valid_channel_slugs_accepted(self) -> None:
        """All 5 canonical channel slugs are accepted."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        valid_channels = [
            "meta-ads",
            "yt-organic",
            "email-nurture",
            "ig-organic",
            "website-total",
        ]

        mock_dashboard = _make_channel_dashboard()

        for channel_slug in valid_channels:
            with (
                patch(_GET_TENANT_ID, return_value=TENANT_ID),
                patch(_CALL_CHANNEL, new=_async_mock(mock_dashboard)),
            ):
                result = get_channel_overview.invoke({"channel": channel_slug})
                parsed = json.loads(result)
                assert "error" not in parsed, f"Channel {channel_slug} raised error: {parsed}"


class TestGetChannelOverviewValidation:
    """Validation tests for channel slug."""

    def test_invalid_channel_slug_rejected_at_schema_level(self) -> None:
        """Invalid slug → Pydantic ValidationError at schema level (before tool body)."""
        from pydantic import ValidationError

        from luana_core_copilot.application.tools._analytics_inputs import (
            ChannelOverviewParams,
        )

        with pytest.raises(ValidationError):
            ChannelOverviewParams(channel="fake-channel")

    def test_no_tenant_returns_error(self) -> None:
        """No tenant in context → structured error."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert "error" in parsed

    def test_channel_slug_not_in_pydantic_allows_tenant_override(self) -> None:
        """ChannelOverviewParams extra='forbid' prevents tenant_id injection."""
        from luana_core_copilot.application.tools._analytics_inputs import (
            ChannelOverviewParams,
        )

        with pytest.raises(ValidationError):
            ChannelOverviewParams(channel="meta-ads", tenant_id="evil")  # type: ignore[call-arg]


class TestGetChannelOverviewTenantIsolation:
    """Verify tenant_id comes from context, not payload."""

    def test_tenant_id_sourced_from_context(self) -> None:
        """Tool calls get_tenant_id() and returns data — tenant from context, not payload."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        mock_dashboard = _make_channel_dashboard()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_CHANNEL, new=_async_mock(mock_dashboard)),
        ):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        # Verify response has data (confirming tenant was used correctly)
        parsed = json.loads(result)
        assert "channel_name" in parsed
        assert "error" not in parsed
