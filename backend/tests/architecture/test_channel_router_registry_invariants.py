"""Architectural fitness — ChannelRouterRegistry runtime contract invariants.

Runtime registry contract (imports actual modules — not pure AST):

1. register_default_channels MUST populate registry such that
   registry.has("telegram") is True after invocation (no real bot token needed
   in test — token_provider stub returns empty string).
2. The registered router MUST satisfy isinstance(router, ChannelRouter) —
   the runtime_checkable Protocol from PR-3.
3. registry.get("nonexistent") MUST raise KeyError.
4. TelegramChannelRouter can be directly constructed and satisfies ChannelRouter.

Uses autouse reset fixture from campaigns conftest to avoid global state leak.
If conftest autouse fixture is not active in this scope, test resets manually.

# [CHANNEL-ROUTER-REGISTRY-INVARIANTS-PR5-S2]
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _reset_channel_registry_arch() -> object:
    """Reset singleton registry before and after each test in this module."""
    from src.modules.campaigns.infrastructure.channels.registry import ChannelRouterRegistry

    ChannelRouterRegistry().reset()
    yield
    ChannelRouterRegistry().reset()


class TestChannelRouterRegistryInvariants:
    """ChannelRouterRegistry runtime Protocol and singleton contracts."""

    def test_telegram_router_satisfies_channel_router_protocol(self) -> None:
        """TelegramChannelRouter satisfies the runtime_checkable ChannelRouter Protocol.

        The ChannelRouter Protocol is decorated with @runtime_checkable (PR-3 domain).
        isinstance() check must return True for TelegramChannelRouter instances.
        """
        from src.modules.campaigns.domain.channel_router import ChannelRouter
        from src.modules.campaigns.infrastructure.channels.telegram import (
            TelegramChannelRouter,
        )

        async def _stub_token_provider(_tenant_id: object) -> str:
            return ""

        router = TelegramChannelRouter(token_provider=_stub_token_provider)
        assert isinstance(router, ChannelRouter), (
            "TelegramChannelRouter must satisfy the ChannelRouter Protocol. "
            "Ensure TelegramChannelRouter implements select_channel() and send() "
            "async methods as defined in domain/channel_router.py."
        )

    def test_register_default_channels_populates_telegram(self) -> None:
        """register_default_channels populates registry with 'telegram' entry."""
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
            register_default_channels,
        )

        async def _stub_token_provider(_tenant_id: object) -> str:
            return ""

        register_default_channels(telegram_token_provider=_stub_token_provider)
        registry = ChannelRouterRegistry()

        assert registry.has("telegram"), (
            "After register_default_channels(), registry.has('telegram') must be True. "
            "WorkerSettings.on_startup and main.py startup hook call this function "
            "to bootstrap the Telegram channel router."
        )

    def test_registered_telegram_router_satisfies_protocol(self) -> None:
        """Router returned by registry.get('telegram') satisfies ChannelRouter Protocol."""
        from src.modules.campaigns.domain.channel_router import ChannelRouter
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
            register_default_channels,
        )

        async def _stub_token_provider(_tenant_id: object) -> str:
            return ""

        register_default_channels(telegram_token_provider=_stub_token_provider)
        registry = ChannelRouterRegistry()
        router = registry.get("telegram")

        assert isinstance(router, ChannelRouter), (
            "registry.get('telegram') must return an object satisfying ChannelRouter "
            "Protocol. The runtime_checkable Protocol verifies that select_channel() "
            "and send() async methods are present."
        )

    def test_registry_get_unknown_channel_raises_key_error(self) -> None:
        """registry.get('nonexistent') raises KeyError for unregistered channels."""
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
        )

        registry = ChannelRouterRegistry()

        with pytest.raises(KeyError, match="nonexistent"):
            registry.get("nonexistent")

    def test_registry_is_singleton(self) -> None:
        """ChannelRouterRegistry() always returns the same instance."""
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
        )

        registry_a = ChannelRouterRegistry()
        registry_b = ChannelRouterRegistry()

        assert registry_a is registry_b, (
            "ChannelRouterRegistry must be a singleton (same object per process). "
            "Multiple calls to ChannelRouterRegistry() must return the same instance."
        )

    def test_registry_reset_clears_registrations(self) -> None:
        """registry.reset() clears all channel registrations (test utility)."""
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
            register_default_channels,
        )

        async def _stub_token_provider(_tenant_id: object) -> str:
            return ""

        register_default_channels(telegram_token_provider=_stub_token_provider)
        registry = ChannelRouterRegistry()
        assert registry.has("telegram"), "Telegram must be registered before reset."

        registry.reset()
        assert not registry.has("telegram"), (
            "After registry.reset(), no channels should be registered. "
            "reset() is used in test autouse fixtures to prevent cross-test state."
        )

    def test_register_invalid_router_raises_type_error(self) -> None:
        """registry.register() raises TypeError for non-Protocol objects."""
        from src.modules.campaigns.infrastructure.channels.registry import (
            ChannelRouterRegistry,
        )

        registry = ChannelRouterRegistry()

        class _NotARouter:
            """Does not implement ChannelRouter Protocol."""

        with pytest.raises(TypeError):
            registry.register("fake_channel", _NotARouter())  # type: ignore[arg-type]
