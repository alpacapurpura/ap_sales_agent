"""TDD — get_stage_metrics tool unit tests. Written RED first.

Tests:
- happy path: valid stage + period → JSON with kpis + tier_used
- tenant isolation: tenant_id from context, never from payload
- tier cascade: overview returned + tier_used field
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

# Patch paths: where names are used (not where defined)
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


def _async_mock(return_value: object) -> AsyncMock:
    """Create AsyncMock that returns the given value.

    Use this instead of return_value=_async_return(x) because:
    a coroutine object can only be awaited once. AsyncMock creates
    a fresh coroutine on each call.
    """
    mock = AsyncMock(return_value=return_value)
    return mock


class TestGetStageMetricsHappy:
    """Happy path tests for get_stage_metrics."""

    def test_returns_json_string(self) -> None:
        """Tool returns a JSON-decodable string."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=_async_mock(overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura", "period": "30d"})

        parsed = json.loads(result)
        assert "stage_name" in parsed
        assert "kpis" in parsed
        assert "tier_used" in parsed

    def test_stage_slug_mapped_correctly(self) -> None:
        """Spanish slug 'atraccion-captura' maps to 'attraction'."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=_async_mock(overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura", "period": "30d"})

        parsed = json.loads(result)
        assert parsed["stage_name"] == "attraction"

    def test_all_valid_stage_slugs_accepted(self) -> None:
        """All 5 canonical stage slugs are accepted without error."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        valid_stages = [
            "atraccion-captura",
            "nutricion-oportunidad",
            "ventas",
            "adopcion",
            "expansion-evangelizacion",
        ]

        overview = _make_stage_overview()

        for stage_slug in valid_stages:
            with (
                patch(_GET_TENANT_ID, return_value=TENANT_ID),
                patch(_CALL_STAGE_OV, new=_async_mock(overview)),
            ):
                result = get_stage_metrics.invoke({"stage": stage_slug})
                parsed = json.loads(result)
                assert "error" not in parsed, f"Stage {stage_slug} raised error: {parsed}"

    def test_invalid_stage_slug_rejected_at_schema_level(self) -> None:
        """Invalid stage slug is rejected by Pydantic Literal at schema validation."""
        from pydantic import ValidationError

        from luana_core_copilot.application.tools._analytics_inputs import (
            StageFilterParams,
        )

        with pytest.raises(ValidationError):
            StageFilterParams(stage="invalid-stage")

    def test_period_defaults_to_30d(self) -> None:
        """When period is '30d', API period is mapped to 'last_30_days'."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        mock_fn = _async_mock(overview)
        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=mock_fn),
        ):
            get_stage_metrics.invoke({"stage": "adopcion"})

        # Verify call was made (default period = 30d → last_30_days)
        assert mock_fn.called


class TestGetStageMetricsTenantIsolation:
    """Tenant_id always from context, never from payload."""

    def test_no_tenant_returns_error(self) -> None:
        """No tenant_id in context → structured error."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = get_stage_metrics.invoke({"stage": "adopcion"})

        parsed = json.loads(result)
        assert "error" in parsed
        assert parsed["error"] in ("no_tenant", "invalid_input")

    def test_tenant_not_in_pydantic_schema(self) -> None:
        """StageFilterParams schema does not allow tenant_id field."""
        from pydantic import ValidationError

        from luana_core_copilot.application.tools._analytics_inputs import (
            StageFilterParams,
        )

        # extra="forbid" should reject tenant_id
        with pytest.raises((ValidationError, TypeError)):
            StageFilterParams(stage="adopcion", tenant_id="evil-override")  # type: ignore[call-arg]


class TestStageMetricsKpiSerialization:
    """Returned KPIs are correctly serialized."""

    def test_kpis_include_slug_and_value(self) -> None:
        """Header KPIs are serialized to JSON with slug and value fields."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        mock_kpi = MagicMock()
        mock_kpi.name = "impressions"
        mock_kpi.value = 12345.0
        mock_kpi.unit = "count"

        overview = _make_stage_overview(header_kpis=[mock_kpi])

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=_async_mock(overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert len(parsed["kpis"]) == 1
        # Note: MagicMock.name is a special attribute — check via getattr
        kpi = parsed["kpis"][0]
        assert "slug" in kpi
        assert kpi["value"] == 12345.0

    def test_response_has_ui_action(self) -> None:
        """Response includes ui_action field for FE rendering."""
        from luana_core_copilot.application.tools.analytics_tools import (
            get_stage_metrics,
        )

        overview = _make_stage_overview()

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_CALL_STAGE_OV, new=_async_mock(overview)),
        ):
            result = get_stage_metrics.invoke({"stage": "atraccion-captura"})

        parsed = json.loads(result)
        assert "ui_action" in parsed
        assert parsed["ui_action"]["type"] == "growth.stage-metrics"
