"""ChannelRouterRegistry — singleton registry of channel implementations.

Singleton is per-process (in-memory). Multi-pod safe because each pod performs
the same bootstrap via ``register_default_channels()`` at startup. Registry
state changes only on deployments, not at runtime.

Razón 1000 clientes: in-memory registry lookup is nanoseconds vs Redis ~5ms
per call on the hot dispatch path (execution worker). Tradeoff justified.

PR-5 PI-1 S2.
"""

from __future__ import annotations

from threading import Lock
from typing import Self

import structlog

from src.modules.campaigns.domain.channel_router import ChannelRouter

logger = structlog.get_logger(__name__)


class ChannelRouterRegistry:
    """Thread-safe singleton registry of ``ChannelRouter`` implementations.

    Usage::

        registry = ChannelRouterRegistry()
        registry.register("telegram", TelegramChannelRouter(...))
        router = registry.get("telegram")

    Test isolation: call ``registry.reset()`` in autouse fixture to prevent
    cross-test global state pollution.

    Multi-pod: every pod calls ``register_default_channels()`` at startup.
    Registry is stable after startup — no runtime mutations expected.
    """

    _instance: ChannelRouterRegistry | None = None
    _lock: Lock = Lock()
    _routers: dict[str, ChannelRouter]

    def __new__(cls) -> Self:
        """Singleton constructor — thread-safe."""
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._routers = {}
                cls._instance = instance
        return cls._instance  # type: ignore[return-value]

    def register(self, channel: str, router: ChannelRouter) -> None:
        """Register a router for a channel slug.

        Silently replaces any existing registration for the same slug.
        Raises ``TypeError`` if ``router`` does not satisfy the
        ``ChannelRouter`` Protocol (runtime_checkable).

        Args:
            channel: Channel slug (e.g. ``"telegram"``, ``"whatsapp"``).
            router: Implementation satisfying the ``ChannelRouter`` Protocol.
        """
        if not isinstance(router, ChannelRouter):
            msg = f"router for {channel!r} debe implementar ChannelRouter Protocol"
            raise TypeError(msg)
        self._routers[channel] = router
        logger.info("channel_router_registered", channel=channel, router_type=type(router).__name__)

    def get(self, channel: str) -> ChannelRouter:
        """Return the router registered for ``channel``.

        Args:
            channel: Channel slug to look up.

        Returns:
            The registered ``ChannelRouter`` implementation.

        Raises:
            KeyError: If no router is registered for the given channel slug.
        """
        try:
            return self._routers[channel]
        except KeyError as exc:
            available = list(self._routers)
            msg = f"channel {channel!r} no registrado en ChannelRouterRegistry. Canales disponibles: {available}"
            raise KeyError(msg) from exc

    def has(self, channel: str) -> bool:
        """Return True if a router is registered for ``channel``."""
        return channel in self._routers

    def reset(self) -> None:
        """Clear all registrations. TEST-ONLY — production code MUST NOT call.

        Use as autouse pytest fixture to prevent cross-test global state:
            @pytest.fixture(autouse=True)
            def reset_channel_registry():
                yield
                ChannelRouterRegistry().reset()
        """
        self._routers.clear()
        logger.debug("channel_router_registry_reset")

    @classmethod
    def instance(cls) -> ChannelRouterRegistry:
        """Return (or create) the singleton instance."""
        return cls()


# Module-level singleton — consumed by workers and orchestrator
channel_router_registry = ChannelRouterRegistry()


def register_default_channels(*, telegram_token_provider: object) -> None:
    """Bootstrap default channel routers. Called at startup (main.py + WorkerSettings).

    ``telegram_token_provider`` — async callable ``(tenant_id: UUID) -> str``
    resolving the bot token for a given tenant.

    For PR-5 dev-app: env var ``TELEGRAM_BOT_TOKEN`` provides a global fallback
    token (smoke-test mode). Tenant-specific tokens are wired in S3+ via the
    connections module.

    Args:
        telegram_token_provider: Async callable resolving bot token by tenant_id.
    """
    from src.modules.campaigns.infrastructure.channels.telegram import TelegramChannelRouter

    registry = ChannelRouterRegistry()
    registry.register(
        "telegram",
        TelegramChannelRouter(token_provider=telegram_token_provider),  # type: ignore[arg-type]
    )
    logger.info("default_channels_registered", channels=["telegram"])
