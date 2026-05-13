"""Factory channel adapter."""

from luana_core_platform.core.config import settings

from .interface import WhatsAppProvider
from .v1 import EvolutionApiV1
from .v2 import EvolutionApiV2


def get_whatsapp_provider(tenant_id: str) -> WhatsAppProvider:
    """Return the correct WhatsApp provider based on configuration."""
    version = settings.EVOLUTION_API_VERSION.lower()
    base_url = settings.EVOLUTION_API_URL
    api_key = settings.EVOLUTION_API_KEY

    if version == "v2":
        return EvolutionApiV2(tenant_id, base_url, api_key)
    return EvolutionApiV1(tenant_id, base_url, api_key)
