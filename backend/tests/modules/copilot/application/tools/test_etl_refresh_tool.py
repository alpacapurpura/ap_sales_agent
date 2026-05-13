"""TDD — trigger_etl_refresh tool unit tests. Written RED first.

Tests:
- rate limit hit → structured error with retry_after_seconds
- confirm flow (requires_confirmation) → structured JSON confirm response
- soft-fail Redis → fail-open (allowed)
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from pydantic import ValidationError

TENANT_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

_GET_TENANT_ID = "luana_core_copilot.application.tools.analytics_tools.get_tenant_id"
_GET_GUARD = "luana_core_copilot.application.tools.analytics_tools._get_etl_refresh_guard"
_CALL_ETL = "luana_core_copilot.application.tools.analytics_tools._call_etl_refresh"


class TestTriggerEtlRefreshHappy:
    """Happy path: allowed refresh queued."""

    def test_allowed_refresh_returns_queued_status(self) -> None:
        """Allowed guard decision + successful ETL → status='queued' in JSON."""
        from luana_core_analytics_engine.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(allowed=True, current_count=1, limit=3)

        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
            patch(_CALL_ETL, new=AsyncMock(return_value={"status": "ok", "run_id": "run-123"})),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads", "confirmed": False})

        parsed = json.loads(result)
        assert parsed.get("status") in ("queued", "ok")

    def test_returns_json_with_current_count_and_limit(self) -> None:
        """Response includes current_count and limit from guard decision."""
        from luana_core_analytics_engine.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(allowed=True, current_count=2, limit=3)
        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
            patch(_CALL_ETL, new=AsyncMock(return_value={"status": "ok", "run_id": "run-456"})),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert "current_count" in parsed
        assert "limit" in parsed


class TestTriggerEtlRefreshRateLimit:
    """Rate limit exceeded → error with retry_after_seconds."""

    def test_rate_limited_returns_error_with_retry_after(self) -> None:
        """Guard blocks → error='rate_limit_exceeded' with retry_after_seconds."""
        from luana_core_analytics_engine.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(
            allowed=False,
            current_count=3,
            limit=3,
            retry_after_seconds=1800,
        )
        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert parsed.get("error") == "rate_limit_exceeded"
        assert parsed.get("retry_after_seconds") == 1800
        assert parsed.get("current_count") == 3
        assert parsed.get("limit") == 3


class TestTriggerEtlRefreshConfirmFlow:
    """Requires confirmation → returns requires_confirmation in JSON."""

    def test_requires_confirmation_returns_correct_status(self) -> None:
        """Guard requires_confirmation → status='requires_confirmation' in JSON."""
        from luana_core_analytics_engine.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(
            allowed=False,
            current_count=2,
            limit=3,
            requires_confirmation=True,
        )
        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads", "confirmed": False})

        parsed = json.loads(result)
        assert parsed.get("status") == "requires_confirmation"
        assert parsed.get("current_count") == 2

    def test_confirmed_true_bypasses_confirmation(self) -> None:
        """confirmed=True passed to guard.check — guard allows, ETL queued."""
        from luana_core_analytics_engine.application.services.etl_refresh_guard import (
            GuardDecision,
        )
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        decision = GuardDecision(allowed=True, current_count=3, limit=3)
        mock_guard = MagicMock()
        mock_guard.check = AsyncMock(return_value=decision)

        with (
            patch(_GET_TENANT_ID, return_value=TENANT_ID),
            patch(_GET_GUARD, return_value=mock_guard),
            patch(_CALL_ETL, new=AsyncMock(return_value={"status": "ok", "run_id": "run-789"})),
        ):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads", "confirmed": True})

        # Guard was called with confirmed=True
        mock_guard.check.assert_called_once_with(TENANT_ID, "meta-ads", confirmed=True)
        parsed = json.loads(result)
        assert "error" not in parsed


class TestTriggerEtlRefreshValidation:
    """Input validation tests."""

    def test_invalid_channel_rejected_at_schema_level(self) -> None:
        """Invalid channel slug → Pydantic ValidationError at schema level (before tool body)."""
        from pydantic import ValidationError

        from luana_core_copilot.application.tools._analytics_inputs import (
            TriggerEtlRefreshParams,
        )

        with pytest.raises(ValidationError):
            TriggerEtlRefreshParams(channel="invalid-channel")

    def test_no_tenant_returns_error(self) -> None:
        """No tenant in context → structured no_tenant error."""
        from luana_core_copilot.application.tools.analytics_tools import (
            trigger_etl_refresh,
        )

        with patch(_GET_TENANT_ID, return_value=None):
            result = trigger_etl_refresh.invoke({"channel": "meta-ads"})

        parsed = json.loads(result)
        assert "error" in parsed

    def test_extra_fields_rejected_by_schema(self) -> None:
        """TriggerEtlRefreshParams extra='forbid' rejects tenant_id override."""
        from luana_core_copilot.application.tools._analytics_inputs import (
            TriggerEtlRefreshParams,
        )

        with pytest.raises(ValidationError):
            TriggerEtlRefreshParams(channel="meta-ads", tenant_id="evil")  # type: ignore[call-arg]
