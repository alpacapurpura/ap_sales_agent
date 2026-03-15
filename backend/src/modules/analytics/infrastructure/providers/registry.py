"""Provider registry — maps provider names to BaseMetricsProvider classes.

Concrete providers (Meta, Google, TikTok, etc.) register themselves here.
The ETL pipeline uses get_provider() to resolve the correct adapter at runtime.
"""

from typing import Dict, Type

from src.modules.analytics.infrastructure.providers.base import BaseMetricsProvider

# Maps provider name strings (e.g. "meta", "google_analytics") to provider classes
PROVIDER_REGISTRY: Dict[str, Type[BaseMetricsProvider]] = {}


def register_provider(name: str, cls: Type[BaseMetricsProvider]) -> None:
    """Register a provider adapter class under the given name.

    Args:
        name: Unique provider identifier (e.g. "meta", "google_analytics").
        cls: BaseMetricsProvider subclass to instantiate for this provider.
    """
    PROVIDER_REGISTRY[name] = cls


def get_provider(provider_name: str) -> BaseMetricsProvider:
    """Resolve and instantiate a provider adapter by name.

    Args:
        provider_name: The provider identifier.

    Returns:
        An instance of the registered BaseMetricsProvider subclass.

    Raises:
        ValueError: If no provider is registered under the given name.
    """
    cls = PROVIDER_REGISTRY.get(provider_name)
    if cls is None:
        registered = ", ".join(sorted(PROVIDER_REGISTRY.keys())) or "(none)"
        raise ValueError(
            f"Unknown provider: '{provider_name}'. "
            f"Registered providers: {registered}"
        )
    return cls()
