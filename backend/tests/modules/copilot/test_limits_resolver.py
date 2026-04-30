"""Tests for CopilotLimitsResolver — resolves effective limits.

4 cases: (a) no override → env defaults; (b) voice override only;
(c) media override only; (d) both overrides.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.copilot.domain.tenant_limits import CopilotTenantLimits


def _make_limits(**kwargs: object) -> CopilotTenantLimits:
    defaults = {
        "tenant_id": uuid4(),
        "voice_rpm_override": None,
        "media_max_bytes_override": None,
        "updated_at": datetime.now(timezone.utc),
        "updated_by_user_id": None,
        "deleted_at": None,
    }
    defaults.update(kwargs)
    return CopilotTenantLimits(**defaults)  # type: ignore[arg-type]


@pytest.fixture
def mock_repo_no_override() -> MagicMock:
    """Repo that returns None (no DB row for tenant)."""
    repo = MagicMock()
    repo.get_by_tenant = AsyncMock(return_value=None)
    return repo


@pytest.fixture
def mock_repo_voice_only() -> MagicMock:
    """Repo that returns override with voice_rpm only."""
    repo = MagicMock()
    repo.get_by_tenant = AsyncMock(return_value=_make_limits(voice_rpm_override=20))
    return repo


@pytest.fixture
def mock_repo_media_only() -> MagicMock:
    """Repo that returns override with media_max_bytes only."""
    repo = MagicMock()
    fifty_mb = 50 * 1024 * 1024
    repo.get_by_tenant = AsyncMock(return_value=_make_limits(media_max_bytes_override=fifty_mb))
    return repo


@pytest.fixture
def mock_repo_both() -> MagicMock:
    """Repo that returns override with both fields."""
    repo = MagicMock()
    repo.get_by_tenant = AsyncMock(
        return_value=_make_limits(voice_rpm_override=15, media_max_bytes_override=30 * 1024 * 1024)
    )
    return repo


@pytest.mark.asyncio
async def test_no_override_uses_env_defaults(mock_repo_no_override: MagicMock) -> None:
    """Case (a): no DB row → returns env defaults."""
    from src.core.config import settings
    from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

    resolver = CopilotLimitsResolver(mock_repo_no_override)
    tenant_id = uuid4()
    effective = await resolver.get_effective(tenant_id)

    assert effective.voice_rpm == settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
    assert effective.media_max_bytes == settings.COPILOT_MEDIA_MAX_BYTES
    assert effective.voice_rpm_is_override is False
    assert effective.media_max_bytes_is_override is False
    assert effective.voice_window_seconds == 60
    assert effective.tenant_id == tenant_id


@pytest.mark.asyncio
async def test_voice_override_only(mock_repo_voice_only: MagicMock) -> None:
    """Case (b): voice override only → voice uses override, media uses env default."""
    from src.core.config import settings
    from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

    resolver = CopilotLimitsResolver(mock_repo_voice_only)
    effective = await resolver.get_effective(uuid4())

    assert effective.voice_rpm == 20
    assert effective.voice_rpm_is_override is True
    assert effective.media_max_bytes == settings.COPILOT_MEDIA_MAX_BYTES
    assert effective.media_max_bytes_is_override is False


@pytest.mark.asyncio
async def test_media_override_only(mock_repo_media_only: MagicMock) -> None:
    """Case (c): media override only → media uses override, voice uses env default."""
    from src.core.config import settings
    from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

    resolver = CopilotLimitsResolver(mock_repo_media_only)
    effective = await resolver.get_effective(uuid4())

    assert effective.voice_rpm == settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
    assert effective.voice_rpm_is_override is False
    assert effective.media_max_bytes == 50 * 1024 * 1024
    assert effective.media_max_bytes_is_override is True


@pytest.mark.asyncio
async def test_both_overrides(mock_repo_both: MagicMock) -> None:
    """Case (d): both overrides → both use override values."""
    from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

    resolver = CopilotLimitsResolver(mock_repo_both)
    effective = await resolver.get_effective(uuid4())

    assert effective.voice_rpm == 15
    assert effective.voice_rpm_is_override is True
    assert effective.media_max_bytes == 30 * 1024 * 1024
    assert effective.media_max_bytes_is_override is True


@pytest.mark.asyncio
async def test_db_error_falls_back_to_env_defaults() -> None:
    """DB error during get_by_tenant → graceful degradation to env defaults."""
    from src.core.config import settings
    from src.modules.copilot.application.services.limits_resolver import CopilotLimitsResolver

    repo = MagicMock()
    repo.get_by_tenant = AsyncMock(side_effect=Exception("DB connection lost"))

    resolver = CopilotLimitsResolver(repo)
    effective = await resolver.get_effective(uuid4())

    assert effective.voice_rpm == settings.COPILOT_VOICE_RATE_LIMIT_PER_MIN
    assert effective.media_max_bytes == settings.COPILOT_MEDIA_MAX_BYTES
    assert effective.voice_rpm_is_override is False
