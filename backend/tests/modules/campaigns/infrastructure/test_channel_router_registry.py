"""Tests for ChannelRouterRegistry — singleton registry + invariants.

TDD RED → GREEN:
- register / get / has happy path
- missing channel raises KeyError with informative message
- duplicate registration silently replaces
- reset() clears all registrations (test isolation)
- register() raises TypeError for non-Protocol objects
- register_default_channels() populates "telegram" entry
- registered router satisfies isinstance(router, ChannelRouter)

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from luana_core_campaigns.domain.channel_router import ChannelRouter, ChannelSendResult
from luana_core_campaigns.infrastructure.channels.registry import (
    ChannelRouterRegistry,
    register_default_channels,
)


# ── Stub ChannelRouter impl for tests ─────────────────────────────────────────


class _StubRouter(ChannelRouter):
    """Minimal ChannelRouter implementation for registry tests."""

    async def select_channel(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        priority: list[str],
    ) -> str | None:
        """Return first priority channel."""
        return priority[0] if priority else None

    async def send(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        content: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> ChannelSendResult:
        """Return stub success result."""
        return ChannelSendResult(success=True, channel=channel)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_registry() -> None:
    """Reset singleton registry after each test to prevent cross-test pollution."""
    yield
    ChannelRouterRegistry().reset()


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_register_and_get_returns_same_instance() -> None:
    """register() then get() returns the exact same router instance."""
    registry = ChannelRouterRegistry()
    router = _StubRouter()
    registry.register("telegram", router)
    assert registry.get("telegram") is router


def test_get_missing_channel_raises_key_error() -> None:
    """get() with unregistered channel raises KeyError with informative message."""
    registry = ChannelRouterRegistry()
    with pytest.raises(KeyError, match="whatsapp"):
        registry.get("whatsapp")


def test_get_missing_channel_key_error_mentions_available() -> None:
    """KeyError message includes list of available channels."""
    registry = ChannelRouterRegistry()
    registry.register("telegram", _StubRouter())
    with pytest.raises(KeyError, match="telegram"):
        registry.get("email")


def test_has_returns_false_for_unregistered() -> None:
    """has() returns False when channel not registered."""
    registry = ChannelRouterRegistry()
    assert registry.has("telegram") is False


def test_has_returns_true_after_register() -> None:
    """has() returns True after register()."""
    registry = ChannelRouterRegistry()
    registry.register("telegram", _StubRouter())
    assert registry.has("telegram") is True


def test_duplicate_registration_replaces_silently() -> None:
    """Registering same channel twice replaces without error."""
    registry = ChannelRouterRegistry()
    router_a = _StubRouter()
    router_b = _StubRouter()
    registry.register("telegram", router_a)
    registry.register("telegram", router_b)  # no exception
    assert registry.get("telegram") is router_b


def test_register_non_protocol_raises_type_error() -> None:
    """register() raises TypeError for object not satisfying ChannelRouter Protocol."""
    registry = ChannelRouterRegistry()
    with pytest.raises(TypeError, match="ChannelRouter Protocol"):
        registry.register("telegram", object())  # type: ignore[arg-type]


def test_reset_clears_all_registrations() -> None:
    """reset() removes all registered routers."""
    registry = ChannelRouterRegistry()
    registry.register("telegram", _StubRouter())
    registry.register("email", _StubRouter())
    registry.reset()
    assert registry.has("telegram") is False
    assert registry.has("email") is False


def test_singleton_returns_same_instance() -> None:
    """ChannelRouterRegistry() always returns the same singleton."""
    r1 = ChannelRouterRegistry()
    r2 = ChannelRouterRegistry()
    assert r1 is r2


def test_register_and_get_multiple_channels() -> None:
    """Multiple channels can be registered and retrieved independently."""
    registry = ChannelRouterRegistry()
    telegram_router = _StubRouter()
    email_router = _StubRouter()
    registry.register("telegram", telegram_router)
    registry.register("email", email_router)
    assert registry.get("telegram") is telegram_router
    assert registry.get("email") is email_router


def test_register_default_channels_registers_telegram() -> None:
    """register_default_channels() populates telegram entry."""
    async_token_provider = AsyncMock(return_value="test-bot-token")
    register_default_channels(telegram_token_provider=async_token_provider)
    registry = ChannelRouterRegistry()
    assert registry.has("telegram")


def test_registered_telegram_router_satisfies_protocol() -> None:
    """Router registered via register_default_channels() satisfies ChannelRouter Protocol."""
    async_token_provider = AsyncMock(return_value="test-bot-token")
    register_default_channels(telegram_token_provider=async_token_provider)
    registry = ChannelRouterRegistry()
    router = registry.get("telegram")
    assert isinstance(router, ChannelRouter)
