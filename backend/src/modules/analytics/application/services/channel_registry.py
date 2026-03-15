"""Channel registry for dynamic, stage-contextual channel rendering.

Maps funnel stages to their relevant channels and determines which
channels a tenant has connected vs. available (showing "Configurar" badge).
Replaces the hardcoded 13-channel list in MetricsService.get_attraction_metrics().
"""

import logging
from typing import Dict, List, Optional, Set
from uuid import UUID

from src.modules.analytics.domain.ports import ConnectionPort

logger = logging.getLogger(__name__)

# Maps provider_name (as used in STAGE_CHANNEL_MAP) to the set of ChannelType
# string values from the connections module that satisfy that provider.
# Plain strings — no import from connections module (DDD boundary).
PROVIDER_TO_CHANNEL_TYPES: Dict[str, Set[str]] = {
    "meta": {"meta", "facebook_page", "instagram_account", "meta_ads_account"},
    "google_analytics": {"google_analytics"},
    "google_ads": {"google_analytics"},  # Google Ads uses the same Google OAuth connection
    "youtube": {"youtube", "youtube_analytics"},
    "tiktok": {"tiktok", "tiktok_ads"},
    "linkedin": set(),        # No ChannelType yet
    "mailerlite": {"mailerlite"},
    "manychat": {"manychat"},
    "whatsapp": {"whatsapp", "whatsapp_cloud"},
    "shopify": {"shopify"},
    "internal": set(),        # Internal sources (CRM, landing) — always "connected"
    "manual": set(),          # Manual sources — always "connected"
}

# Stage-to-channel mapping. Each channel definition includes metadata
# needed by both backend (ETL routing) and frontend (rendering).
STAGE_CHANNEL_MAP: Dict[str, List[dict]] = {
    "attraction": [
        # Organic social: reach + engagement
        {"slug": "ig-organic", "name": "Instagram Organic", "channel_type": "social", "source_label": "Instagram", "provider_name": "meta", "metric_names": ["reach", "engagement"]},
        {"slug": "yt-organic", "name": "YouTube Organic", "channel_type": "social", "source_label": "YouTube", "provider_name": "youtube", "metric_names": ["reach", "engagement"]},
        {"slug": "fb-organic", "name": "Facebook Organic", "channel_type": "social", "source_label": "Facebook", "provider_name": "meta", "metric_names": ["reach", "engagement"]},
        {"slug": "tiktok-organic", "name": "TikTok Organic", "channel_type": "social", "source_label": "TikTok", "provider_name": "tiktok", "metric_names": ["reach", "engagement"]},
        {"slug": "linkedin-organic", "name": "LinkedIn Organic", "channel_type": "social", "source_label": "LinkedIn", "provider_name": "linkedin", "metric_names": ["reach", "engagement"]},
        # GA4 search: sessions + users
        {"slug": "google-organic", "name": "Google Organic", "channel_type": "search", "source_label": "Google Search", "provider_name": "google_analytics", "metric_names": ["sessions", "users"]},
        {"slug": "direct", "name": "Direct Traffic", "channel_type": "direct", "source_label": "Direct", "provider_name": "google_analytics", "metric_names": ["sessions", "users"]},
        {"slug": "ai-search-organic", "name": "AI Search Organic", "channel_type": "search", "source_label": "AI Search", "provider_name": "google_analytics", "metric_names": ["sessions", "users"]},
        # Paid: reach + clicks + conversions + spend
        {"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid", "source_label": "Meta Ads", "provider_name": "meta", "metric_names": ["reach", "clicks", "conversions", "spend"]},
        {"slug": "google-ads", "name": "Google Ads", "channel_type": "paid", "source_label": "Google Ads", "provider_name": "google_ads", "metric_names": ["reach", "clicks", "conversions", "spend"]},
        {"slug": "tiktok-ads", "name": "TikTok Ads", "channel_type": "paid", "source_label": "TikTok Ads", "provider_name": "tiktok", "metric_names": ["reach", "clicks", "conversions", "spend"]},
        {"slug": "yt-ads", "name": "YouTube Ads", "channel_type": "paid", "source_label": "YouTube Ads", "provider_name": "google_ads", "metric_names": ["reach", "clicks", "conversions", "spend"]},
        # Outbound: contacts + responses
        {"slug": "cold-contact", "name": "Cold Contact", "channel_type": "outbound", "source_label": "Cold Outreach", "provider_name": "manual", "metric_names": ["contacts", "responses"]},
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
        connected_channel_types = {conn.channel_type for conn in active_connections}

        connected = []
        available = []

        for ch in channels:
            provider_name = ch.get("provider_name", "")

            # Internal and manual providers are always connected
            if provider_name in ("internal", "manual"):
                connected.append({**ch, "connected": True})
                continue

            # Look up which ChannelType values satisfy this provider
            provider_types = PROVIDER_TO_CHANNEL_TYPES.get(provider_name)
            if provider_types is None:
                logger.warning(
                    "Unknown provider_name '%s' for channel slug '%s' — classifying as available",
                    provider_name,
                    ch.get("slug"),
                )
                available.append(
                    {**ch, "connected": False, "badge_type": "configurar"}
                )
                continue

            # Check if any of the provider's channel types are connected
            if provider_types & connected_channel_types:
                connected.append({**ch, "connected": True})
            else:
                available.append(
                    {**ch, "connected": False, "badge_type": "configurar"}
                )

        return {"connected": connected, "available": available}
