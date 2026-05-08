"""TDD — Observability tests for analytics tools. Written RED first.

Tests:
- Each tool returns JSON (no raw exceptions leaked)
- Tools don't return PII fields (email/phone/address)
- Tools return aggregated metrics only
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
PII_FIELDS = {"email", "phone", "address", "mobile", "telephone", "ssn"}

_GET_TENANT_ID = "src.modules.copilot.application.tools.analytics_tools.get_tenant_id"
_CALL_STAGE_OV = "src.modules.copilot.application.tools.analytics_tools._call_stage_overview"
_CALL_CHANNEL = "src.modules.copilot.application.tools.analytics_tools._call_channel_dashboard"
_GET_GUARD = "src.modules.copilot.application.tools.analytics_tools._get_etl_refresh_guard"
_CALL_ETL = "src.modules.copilot.application.tools.analytics_tools._call_etl_refresh"


class TestNoLeakOfPii:
    """Tools must not include PII fields in their JSON output."""

    def test_get_stage_metrics_no_pii_fields(self) -> None:
        """get_stage_metrics response contains no PII field names."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = MagicMock()
        overview.stage = "attraction"
        overview.period = "last_30_days"
        overview.header_kpis = []
        overview.channels = []
        overview.groups = []

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=AsyncMock(return_value=overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        for pii_field in PII_FIELDS:
            assert pii_field not in parsed, f"PII field '{pii_field}' found in response"

    def test_get_channel_overview_no_pii_fields(self) -> None:
        """get_channel_overview response contains no PII field names."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        dashboard = MagicMock()
        dashboard.channel_slug = "meta-ads"
        dashboard.channel_name = "Meta Ads"
        dashboard.period = "30d"
        dashboard.kpis = []

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_CHANNEL, new=AsyncMock(return_value=dashboard)),
        ):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        for pii_field in PII_FIELDS:
            assert pii_field not in parsed, f"PII field '{pii_field}' found in response"


class TestNoRawExceptionLeak:
    """Tools return structured JSON even on internal errors, not raw exceptions."""

    def test_get_stage_metrics_exception_returns_structured_error(self) -> None:
        """RuntimeError in _call_stage_overview → structured JSON error response."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        async def _raise(*args, **kwargs) -> None:
            msg = "DB connection error"
            raise RuntimeError(msg)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=_raise),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        # Must be valid JSON (not a raw exception string)
        parsed = json.loads(result)
        assert "error" in parsed

    def test_get_channel_overview_exception_returns_structured_error(self) -> None:
        """RuntimeError in _call_channel_dashboard → structured JSON error response."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        async def _raise(*args, **kwargs) -> None:
            msg = "Service down"
            raise RuntimeError(msg)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_CHANNEL, new=_raise),
        ):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert "error" in parsed

    def test_trigger_etl_refresh_exception_returns_structured_error(self) -> None:
        """RuntimeError in ETL call → structured JSON error response."""
        from src.modules.analytics.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from src.modules.copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(allowed=True, current_count=1, limit=3)
        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        async def _raise(*args, **kwargs) -> None:
            msg = "ETL service down"
            raise RuntimeError(msg)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
            patch(_CALL_ETL, new=_raise),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads"})

        # Should return JSON, not raise
        parsed = json.loads(result)
        assert "error" in parsed


class TestToolsReturnJsonString:
    """All tools must return str (JSON) per LangChain tool contract."""

    def test_get_stage_metrics_returns_string(self) -> None:
        """get_stage_metrics always returns str (no_tenant path)."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = get_stage_metrics.invoke({"stage": "adopcion"})

        assert isinstance(result, str)

    def test_get_channel_overview_returns_string(self) -> None:
        """get_channel_overview always returns str (no_tenant path)."""
        from src.modules.copilot.application.tools.analytics_tools import (
            get_channel_overview,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = get_channel_overview.invoke({"channel": "meta-ads"})

        assert isinstance(result, str)

    def test_trigger_etl_refresh_returns_string(self) -> None:
        """trigger_etl_refresh always returns str (no_tenant path)."""
        from src.modules.copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads"})

        assert isinstance(result, str)
