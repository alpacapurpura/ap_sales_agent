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


def _register_all() -> None:
    """Register all concrete provider adapters.

    Uses late-binding imports to avoid circular imports and ensure
    providers are registered at module import time.
    """
    from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider
    from src.modules.analytics.infrastructure.providers.google_analytics_provider import GoogleAnalyticsProvider
    from src.modules.analytics.infrastructure.providers.google_ads_provider import GoogleAdsProvider
    from src.modules.analytics.infrastructure.providers.tiktok_provider import TikTokProvider
    from src.modules.analytics.infrastructure.providers.youtube_provider import YouTubeProvider
    from src.modules.analytics.infrastructure.providers.crm_internal_provider import CRMInternalProvider

    register_provider("meta", MetaProvider)
    register_provider("google_analytics", GoogleAnalyticsProvider)
    register_provider("google_ads", GoogleAdsProvider)
    register_provider("tiktok", TikTokProvider)
    register_provider("youtube", YouTubeProvider)
    register_provider("crm_internal", CRMInternalProvider)


_register_all()
