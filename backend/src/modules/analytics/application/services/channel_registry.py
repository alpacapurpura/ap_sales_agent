"""Channel registry for dynamic, stage-contextual channel rendering.

Maps funnel stages to their relevant channels and determines which
channels a tenant has connected vs. available (showing "Configurar" badge).
Replaces the hardcoded 13-channel list in MetricsService.get_attraction_metrics().
"""

from typing import Dict, List, Optional
from uuid import UUID

from src.modules.analytics.domain.ports import ConnectionPort

# Stage-to-channel mapping. Each channel definition includes metadata
# needed by both backend (ETL routing) and frontend (rendering).
STAGE_CHANNEL_MAP: Dict[str, List[dict]] = {
    "attraction": [
        {"slug": "ig-organic", "name": "Instagram Organic", "channel_type": "social", "source_label": "Instagram", "provider_name": "meta"},
        {"slug": "yt-organic", "name": "YouTube Organic", "channel_type": "social", "source_label": "YouTube", "provider_name": "youtube"},
        {"slug": "fb-organic", "name": "Facebook Organic", "channel_type": "social", "source_label": "Facebook", "provider_name": "meta"},
        {"slug": "tiktok-organic", "name": "TikTok Organic", "channel_type": "social", "source_label": "TikTok", "provider_name": "tiktok"},
        {"slug": "linkedin-organic", "name": "LinkedIn Organic", "channel_type": "social", "source_label": "LinkedIn", "provider_name": "linkedin"},
        {"slug": "google-organic", "name": "Google Organic", "channel_type": "search", "source_label": "Google Search", "provider_name": "google_analytics"},
        {"slug": "direct", "name": "Direct Traffic", "channel_type": "direct", "source_label": "Direct", "provider_name": "google_analytics"},
        {"slug": "ai-search-organic", "name": "AI Search Organic", "channel_type": "search", "source_label": "AI Search", "provider_name": "google_analytics"},
        {"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid", "source_label": "Meta Ads", "provider_name": "meta"},
        {"slug": "google-ads", "name": "Google Ads", "channel_type": "paid", "source_label": "Google Ads", "provider_name": "google_ads"},
        {"slug": "tiktok-ads", "name": "TikTok Ads", "channel_type": "paid", "source_label": "TikTok Ads", "provider_name": "tiktok"},
        {"slug": "yt-ads", "name": "YouTube Ads", "channel_type": "paid", "source_label": "YouTube Ads", "provider_name": "google_ads"},
        {"slug": "cold-contact", "name": "Cold Contact", "channel_type": "outbound", "source_label": "Cold Outreach", "provider_name": "manual"},
    ],
    "capture": [
        {"slug": "landing-form", "name": "Landing Page Form", "channel_type": "form", "source_label": "Landing Page", "provider_name": "internal"},
        {"slug": "mailerlite", "name": "MailerLite", "channel_type": "email", "source_label": "MailerLite", "provider_name": "mailerlite"},
        {"slug": "ig-dm", "name": "Instagram DM", "channel_type": "messaging", "source_label": "Instagram DM", "provider_name": "meta"},
        {"slug": "fb-messenger", "name": "Facebook Messenger", "channel_type": "messaging", "source_label": "Messenger", "provider_name": "meta"},
        {"slug": "tiktok-dm", "name": "TikTok DM", "channel_type": "messaging", "source_label": "TikTok DM", "provider_name": "tiktok"},
        {"slug": "whatsapp-inbound", "name": "WhatsApp Inbound", "channel_type": "messaging", "source_label": "WhatsApp", "provider_name": "whatsapp"},
    ],
    "nurture": [
        {"slug": "mailerlite", "name": "MailerLite", "channel_type": "email", "source_label": "MailerLite", "provider_name": "mailerlite"},
        {"slug": "manychat", "name": "ManyChat", "channel_type": "automation", "source_label": "ManyChat", "provider_name": "manychat"},
    ],
    "sales": [
        {"slug": "sales-agent", "name": "Sales Agent", "channel_type": "ai", "source_label": "AI SDR", "provider_name": "internal"},
        {"slug": "shopify", "name": "Shopify", "channel_type": "ecommerce", "source_label": "Shopify", "provider_name": "shopify"},
    ],
    "delivery": [
        {"slug": "email-delivery", "name": "Email Delivery", "channel_type": "email", "source_label": "Email", "provider_name": "mailerlite"},
    ],
    "retention": [
        {"slug": "email-retention", "name": "Retention Emails", "channel_type": "email", "source_label": "Email", "provider_name": "mailerlite"},
    ],
    "referral": [
        {"slug": "referral-program", "name": "Referral Program", "channel_type": "referral", "source_label": "Referrals", "provider_name": "internal"},
    ],
}


def get_stage_channels(stage_slug: str) -> List[dict]:
    """Return channel definitions for a given funnel stage.

    Returns an empty list for unknown stages.
    """
    return STAGE_CHANNEL_MAP.get(stage_slug, [])


class ChannelRegistry:
    """Determines connected vs. available channels for a tenant and stage.

    Uses ConnectionPort to check which providers the tenant has connected,
    then splits stage channels into:
    - connected: channels with active provider connections
    - available: channels without connections (show "Configurar" badge)
    """

    def __init__(self, connection_port: ConnectionPort):
        self._connection_port = connection_port

    async def get_stage_channels(self, stage_slug: str) -> List[dict]:
        """Return all channel definitions for a stage (static mapping)."""
        return get_stage_channels(stage_slug)

    async def get_available_channels(
        self, tenant_id: UUID, stage_slug: str
    ) -> Dict[str, List[dict]]:
        """Split stage channels into connected and available for a tenant.

        Returns:
            {
                "connected": [{"slug": ..., "connected": True, ...}, ...],
                "available": [{"slug": ..., "connected": False, "badge_type": "configurar", ...}, ...]
            }
        """
        channels = get_stage_channels(stage_slug)
        active_connections = await self._connection_port.list_active_connections(
            tenant_id
        )

        # Build a set of connected channel_types for fast lookup
        connected_types = {conn.channel_type for conn in active_connections}

        connected = []
        available = []

        for ch in channels:
            if ch["slug"] in connected_types:
                connected.append({**ch, "connected": True})
            else:
                available.append(
                    {**ch, "connected": False, "badge_type": "configurar"}
                )

        return {"connected": connected, "available": available}
