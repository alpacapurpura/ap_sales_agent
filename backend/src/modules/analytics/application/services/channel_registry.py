"""Channel registry for dynamic, stage-contextual channel rendering.

Maps funnel stages to their relevant channels and determines which
channels a tenant has connected vs. available (showing "Configurar" badge).
Replaces the hardcoded 13-channel list in MetricsService.get_attraction_metrics().
"""

from uuid import UUID

import structlog

from src.modules.analytics.domain.ports import ConnectionPort

logger = structlog.get_logger(__name__)

# Maps provider_name (as used in STAGE_CHANNEL_MAP) to the set of ChannelType
# string values from the connections module that satisfy that provider.
# Plain strings — no import from connections module (DDD boundary).
PROVIDER_TO_CHANNEL_TYPES: dict[str, set[str]] = {
    "meta": {"meta", "facebook_page", "instagram_account", "meta_ads_account"},
    "google_analytics": {"google_analytics"},
    "google_ads": {
        "google_analytics",
    },  # Google Ads uses the same Google OAuth connection
    "youtube": {"youtube", "youtube_analytics"},
    "tiktok": {"tiktok", "tiktok_ads"},
    "linkedin": set(),  # No ChannelType yet
    "email_marketing": {"mailerlite", "mailchimp", "activecampaign"},
    "mailerlite": {
        "mailerlite",
        "mailchimp",
        "activecampaign",
    },  # alias so PROVIDER_REGISTRY key resolves
    "manychat": {"manychat"},
    "whatsapp": {"whatsapp", "whatsapp_cloud"},
    "shopify": {"shopify"},
    "internal": set(),  # Internal sources (CRM, landing) — always "connected"
    "manual": set(),  # Manual sources — always "connected"
    "meta_pixel": {"meta_pixel"},
    "search_console": {"google_analytics"},  # Uses same Google OAuth as GA4
}

# Inverse mapping: channel_type_value → set of provider_names that need it.
# E.g. "google_analytics" → {"google_analytics", "google_ads"}
CHANNEL_TYPE_TO_PROVIDERS: dict[str, set[str]] = {}
for _prov, _types in PROVIDER_TO_CHANNEL_TYPES.items():
    for _ct in _types:
        CHANNEL_TYPE_TO_PROVIDERS.setdefault(_ct, set()).add(_prov)

# Stage-to-channel mapping. Each channel definition includes metadata
# needed by both backend (ETL routing) and frontend (rendering).
STAGE_CHANNEL_MAP: dict[str, list[dict]] = {
    "attraction": [
        # Organic social: reach + engagement
        {
            "slug": "ig-organic",
            "name": "Instagram Organic",
            "channel_type": "social",
            "source_label": "Instagram",
            "provider_name": "meta",
            "metric_names": [
                # Summary (ChannelRow) — primeras 3
                "reach",
                "total_interactions",
                "ig_followers_count",
                # Visibilidad
                "ig_views",
                "ig_follows_and_unfollows",
                "ig_follows_gained",
                "ig_follows_lost",
                "ig_media_count",
                # Engagement detalle
                "ig_likes",
                "ig_comments",
                "ig_shares",
                "ig_saves",
                "ig_replies",
                "ig_reposts",
                # Perfil
                "ig_accounts_engaged",
                "ig_profile_links_taps",
                # Demografía
                "ig_follower_demographics",
                "ig_engaged_audience_demographics",
            ],
        },
        {
            "slug": "yt-organic",
            "name": "YouTube Organic",
            "channel_type": "social",
            "source_label": "YouTube",
            "provider_name": "youtube",
            "metric_names": [
                "views",
                "engagement",
                "subscribers_gained",
                "watch_time_minutes",
                "avg_view_duration",
                "avg_view_percentage",
                "comments",
                "shares",
                "subscribers_lost",
                "card_clicks",
                "card_impressions",
                "card_click_rate",
                "end_screen_clicks",
                "end_screen_impressions",
                "end_screen_click_rate",
            ],
        },
        {
            "slug": "fb-organic",
            "name": "Facebook Organic",
            "channel_type": "social",
            "source_label": "Facebook",
            "provider_name": "meta",
            "metric_names": ["reach", "engagement"],
        },
        {
            "slug": "tiktok-organic",
            "name": "TikTok Organic",
            "channel_type": "social",
            "source_label": "TikTok",
            "provider_name": "tiktok",
            "metric_names": ["video_views", "engagement"],
        },
        {
            "slug": "linkedin-organic",
            "name": "LinkedIn Organic",
            "channel_type": "social",
            "source_label": "LinkedIn",
            "provider_name": "linkedin",
            "metric_names": ["reach", "engagement"],
        },
        # GA4 search: sessions + users
        {
            "slug": "google-organic",
            "name": "Google Organic",
            "channel_type": "search",
            "source_label": "Google Search",
            "provider_name": "google_analytics",
            "metric_names": [
                "sessions",
                "users",
                "bounceRate",
                "engagedSessions",
                "newUsers",
                "screenPageViews",
                "activeUsers",
                "engagementRate",
            ],
        },
        {
            "slug": "direct",
            "name": "Direct Traffic",
            "channel_type": "direct",
            "source_label": "Direct",
            "provider_name": "google_analytics",
            "metric_names": [
                "sessions",
                "users",
                "bounceRate",
                "engagedSessions",
                "newUsers",
                "screenPageViews",
                "activeUsers",
                "engagementRate",
            ],
        },
        {
            "slug": "ai-search-organic",
            "name": "AI Search Organic",
            "channel_type": "search",
            "source_label": "AI Search",
            "provider_name": "google_analytics",
            "metric_names": [
                "sessions",
                "users",
                "bounceRate",
                "engagedSessions",
                "newUsers",
                "screenPageViews",
                "activeUsers",
                "engagementRate",
            ],
        },
        {
            "slug": "search-console",
            "name": "Google Search Console",
            "channel_type": "search",
            "source_label": "Search Console",
            "provider_name": "search_console",
            "metric_names": [
                "impressions",
                "clicks",
                "ctr",
                "avg_position",
                "top_queries",
            ],
        },
        # Paid channel — reach, clicks, conversions, spend
        {
            "slug": "meta-ads",
            "name": "Meta Ads",
            "channel_type": "paid",
            "source_label": "Meta Ads",
            "provider_name": "meta",
            "metric_names": [
                # Summary (ChannelRow) — primeras 3
                "reach",
                "spend",
                "meta_purchase_roas",
                # Rendimiento
                "impressions",
                "clicks",
                "meta_inline_link_clicks",
                "meta_outbound_clicks",
                "meta_post_engagement",
                "meta_landing_page_views",
                # Costos
                "ctr",
                "cpm",
                "cpc",
                "meta_cpp",
                "frequency",
                "meta_cost_per_link_click",
                "meta_cost_per_outbound_click",
                # Conversiones
                "conversions",
                "meta_leads",
                "meta_add_to_cart",
                "meta_initiate_checkout",
                "meta_registrations",
                "meta_view_content",
                "meta_conversations_started",
                # Valor & ROAS
                "meta_conversion_value",
                "meta_purchase_roas",
                "meta_cost_per_purchase",
                "meta_cost_per_lead",
                # Video
                "meta_video_views",
                "meta_video_p25",
                "meta_video_p50",
                "meta_video_p75",
                "meta_video_p100",
                "meta_video_30sec",
                "meta_video_avg_watch_time",
                # Breakdowns
                "meta_reach_by_age",
                "meta_spend_by_age",
                "meta_impressions_by_age",
                "meta_reach_by_gender",
                "meta_spend_by_gender",
                "meta_impressions_by_gender",
                "meta_reach_by_placement",
                "meta_spend_by_placement",
                "meta_impressions_by_placement",
            ],
        },
        {
            "slug": "google-ads",
            "name": "Google Ads",
            "channel_type": "paid",
            "source_label": "Google Ads",
            "provider_name": "google_ads",
            "metric_names": [
                "impressions",
                "clicks",
                "conversions",
                "spend",
                "ctr",
                "cpc",
                "conversion_value",
                "search_terms",
            ],
        },
        {
            "slug": "tiktok-ads",
            "name": "TikTok Ads",
            "channel_type": "paid",
            "source_label": "TikTok Ads",
            "provider_name": "tiktok",
            "metric_names": ["reach", "clicks", "conversions", "spend"],
        },
        {
            "slug": "yt-ads",
            "name": "YouTube Ads",
            "channel_type": "paid",
            "source_label": "YouTube Ads",
            "provider_name": "google_ads",
            "metric_names": [
                "impressions",
                "clicks",
                "conversions",
                "spend",
                "ctr",
                "cpc",
                "conversion_value",
            ],
        },
        # Outbound channel — contacts, responses
        {
            "slug": "cold-contact",
            "name": "Cold Contact",
            "channel_type": "outbound",
            "source_label": "Cold Outreach",
            "provider_name": "manual",
            "metric_names": ["contacts", "responses"],
        },
        # ManyChat comment triggers -> attraction
        {
            "slug": "manychat-comments",
            "name": "ManyChat Comment Triggers",
            "channel_type": "social",
            "source_label": "ManyChat",
            "provider_name": "manychat",
            "metric_names": ["comment_triggers", "dm_opens"],
        },
        # Website: site-wide aggregate from GA4
        {
            "slug": "website-total",
            "name": "Tu Sitio Web",
            "channel_type": "website",
            "source_label": "Google Analytics",
            "provider_name": "google_analytics",
            "metric_names": [
                "sessions",
                "users",
                "bounceRate",
                "engagedSessions",
                "newUsers",
                "screenPageViews",
                "activeUsers",
                "engagementRate",
                "averageSessionDuration",
                "conversions",
                "top_pages",
                "traffic_sources",
                "device_split",
            ],
        },
        # Website: Meta Pixel events (Phase 2)
        {
            "slug": "meta-pixel",
            "name": "Meta Pixel",
            "channel_type": "website",
            "source_label": "Meta Pixel",
            "provider_name": "meta_pixel",
            "metric_names": [
                "pixel_pageviews",
                "pixel_view_content",
                "pixel_leads",
                "pixel_add_to_cart",
                "pixel_purchases",
            ],
        },
    ],
    "capture": [
        {
            "slug": "landing-form",
            "name": "Landing Page Form",
            "channel_type": "form",
            "source_label": "Landing Page",
            "provider_name": "internal",
        },
        {
            "slug": "email-capture",
            "name": "Email Capture",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "new_subscribers",
                "active_subscribers",
                "form_conversions",
                "form_conversion_rate",
            ],
        },
        {
            "slug": "ig-dm",
            "name": "Instagram DM",
            "channel_type": "messaging",
            "source_label": "Instagram DM",
            "provider_name": "meta",
        },
        {
            "slug": "fb-messenger",
            "name": "Facebook Messenger",
            "channel_type": "messaging",
            "source_label": "Messenger",
            "provider_name": "meta",
        },
        {
            "slug": "tiktok-dm",
            "name": "TikTok DM",
            "channel_type": "messaging",
            "source_label": "TikTok DM",
            "provider_name": "tiktok",
        },
        {
            "slug": "whatsapp-inbound",
            "name": "WhatsApp Inbound",
            "channel_type": "messaging",
            "source_label": "WhatsApp",
            "provider_name": "whatsapp",
        },
        {
            "slug": "manychat-ig",
            "name": "ManyChat Instagram",
            "channel_type": "messaging",
            "source_label": "ManyChat IG",
            "provider_name": "manychat",
            "metric_names": [
                "new_subscribers",
                "leads",
                "conversations",
                "conversion_rate",
            ],
        },
        {
            "slug": "manychat-wa",
            "name": "ManyChat WhatsApp",
            "channel_type": "messaging",
            "source_label": "ManyChat WA",
            "provider_name": "manychat",
            "metric_names": [
                "new_subscribers",
                "leads",
                "conversations",
                "conversion_rate",
            ],
        },
    ],
    "nurture": [
        # Retargeting Omnichannel
        {
            "slug": "meta-retargeting",
            "name": "Meta Retargeting",
            "channel_type": "retargeting",
            "source_label": "Meta Ads",
            "provider_name": "meta",
            "metric_names": ["reach", "clicks", "spend"],
        },
        {
            "slug": "google-retargeting",
            "name": "Google Retargeting",
            "channel_type": "retargeting",
            "source_label": "Google Ads",
            "provider_name": "google_ads",
            "metric_names": ["impressions", "clicks", "spend", "ctr", "cpc"],
        },
        {
            "slug": "tiktok-retargeting",
            "name": "TikTok Retargeting",
            "channel_type": "retargeting",
            "source_label": "TikTok Ads",
            "provider_name": "tiktok",
            "metric_names": ["reach", "clicks", "spend"],
        },
        # Automatizacion
        {
            "slug": "email-nurture",
            "name": "Email Nurturing",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "emails_sent",
                "unique_opens",
                "open_rate",
                "click_rate",
                "click_to_open_rate",
                "unsubscribe_rate",
                "bounce_rate",
                "spam_reports",
            ],
        },
        {
            "slug": "ai-sdr",
            "name": "AI SDR",
            "channel_type": "automation",
            "source_label": "AI SDR",
            "provider_name": "internal",
            "metric_names": ["followups", "response_rate"],
        },
        {
            "slug": "manychat-sequences",
            "name": "ManyChat Sequences",
            "channel_type": "automation",
            "source_label": "ManyChat",
            "provider_name": "manychat",
            "metric_names": ["sequences_sent", "response_rate", "qualified_leads"],
        },
    ],
    "opportunity": [
        # Checkout group
        {
            "slug": "checkout-init",
            "name": "Checkout Iniciado",
            "channel_type": "checkout",
            "source_label": "Shopify",
            "provider_name": "shopify",
            "metric_names": ["count", "value"],
        },
        {
            "slug": "abandoned-cart",
            "name": "Carrito Abandonado",
            "channel_type": "checkout",
            "source_label": "Shopify",
            "provider_name": "shopify",
            "metric_names": ["count", "value", "abandonment_rate"],
        },
        # Payment Links group
        {
            "slug": "link-enviado",
            "name": "Link de Pago Enviado",
            "channel_type": "payment_link",
            "source_label": "Sales Agent",
            "provider_name": "internal",
            "metric_names": ["count", "value"],
        },
        {
            "slug": "checkout-lp",
            "name": "Checkout Landing Page",
            "channel_type": "payment_link",
            "source_label": "Landing Page",
            "provider_name": "internal",
            "metric_names": ["count", "value"],
        },
        # Qualification group
        {
            "slug": "meeting-booked",
            "name": "Reuniones Agendadas",
            "channel_type": "qualification",
            "source_label": "Scheduling",
            "provider_name": "internal",
            "metric_names": ["booked", "completed", "no_show", "rescheduled"],
        },
        {
            "slug": "manychat-bofu",
            "name": "ManyChat BOFU",
            "channel_type": "qualification",
            "source_label": "ManyChat",
            "provider_name": "manychat",
            "metric_names": [
                "meetings_requested",
                "bofu_flows_triggered",
                "consultations",
            ],
        },
        {
            "slug": "email-launch",
            "name": "Email Launch",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "emails_sent",
                "open_rate",
                "click_rate",
                "click_to_open_rate",
                "unique_clicks",
                "unsubscribes",
            ],
        },
    ],
    "sales": [
        {
            "slug": "sales-agent",
            "name": "Sales Agent",
            "channel_type": "ai",
            "source_label": "AI SDR",
            "provider_name": "internal",
        },
        {
            "slug": "shopify",
            "name": "Shopify",
            "channel_type": "ecommerce",
            "source_label": "Shopify",
            "provider_name": "shopify",
            "metric_names": [
                "revenue",
                "order_count",
                "avg_order_value",
                "units_sold",
                "total_discounts",
                "net_sales",
                "refund_amount",
                "refund_count",
                "shipping_revenue",
                "discount_usage_count",
                "repeat_customers",
            ],
        },
    ],
    "adoption": [
        {
            "slug": "product-usage",
            "name": "Uso del Producto",
            "channel_type": "engagement",
            "source_label": "CRM",
            "provider_name": "internal",
        },
        {
            "slug": "email-onboarding",
            "name": "Email Onboarding",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "emails_sent",
                "open_rate",
                "click_rate",
                "automation_completed",
                "completion_rate",
            ],
        },
    ],
    "expansion": [
        {
            "slug": "renewals",
            "name": "Renovaciones",
            "channel_type": "recurring",
            "source_label": "CRM",
            "provider_name": "internal",
        },
        {
            "slug": "upsell",
            "name": "Ventas Adicionales",
            "channel_type": "growth",
            "source_label": "CRM",
            "provider_name": "internal",
        },
        {
            "slug": "email-upsell",
            "name": "Email Upsell",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": ["emails_sent", "open_rate", "click_rate", "unique_clicks"],
        },
    ],
    "delivery": [
        {
            "slug": "email-delivery",
            "name": "Email Delivery",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "emails_sent",
                "open_rate",
                "click_rate",
                "completion_rate",
            ],
        },
    ],
    "retention": [
        {
            "slug": "email-retention",
            "name": "Retention Emails",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": [
                "emails_sent",
                "open_rate",
                "reactivation_rate",
                "unsubscribe_rate",
            ],
        },
    ],
    "referral": [
        {
            "slug": "referral-program",
            "name": "Referral Program",
            "channel_type": "referral",
            "source_label": "Referrals",
            "provider_name": "internal",
        },
    ],
    "evangelization": [
        {
            "slug": "referral-organic",
            "name": "Referidos Organicos",
            "channel_type": "referral",
            "source_label": "Codigos de Referido",
            "provider_name": "internal",
            "metric_names": ["referrals_sent", "conversions", "revenue"],
        },
        {
            "slug": "nps-surveys",
            "name": "Encuestas NPS",
            "channel_type": "survey",
            "source_label": "NPS",
            "provider_name": "internal",
            "metric_names": ["score", "response_rate", "promoters"],
        },
        {
            "slug": "email-referral",
            "name": "Email Referral",
            "channel_type": "email",
            "source_label": "Email",
            "provider_name": "email_marketing",
            "metric_names": ["emails_sent", "open_rate", "forwards", "click_rate"],
        },
    ],
}


# Channels planned for future implementation (provider not yet active)
PLANNED_CHANNEL_SLUGS: set[str] = {
    # LinkedIn (no ChannelType yet)
    "linkedin-organic",
    # ManyChat channels (stub provider, data arrives via webhook only)
    "manychat-comments",
    "manychat-ig",
    "manychat-wa",
    "manychat-sequences",
    "manychat-bofu",
    # Internal scheduling/referral (not yet extracted)
    "meeting-booked",
    # AI SDR (internal, future)
    "ai-sdr",
}


def get_stage_channels(stage_slug: str) -> list[dict]:
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

    def __init__(self, connection_port: ConnectionPort) -> None:
        """Initialize channel registry."""
        self._connection_port = connection_port

    async def get_stage_channels(self, stage_slug: str) -> list[dict]:
        """Return all channel definitions for a stage (static mapping)."""
        return get_stage_channels(stage_slug)

    async def get_available_channels(
        self,
        tenant_id: UUID,
        stage_slug: str,
    ) -> dict[str, list[dict]]:
        """Split stage channels into connected and available for a tenant.

        Returns:
            {
                "connected": [{"slug": ..., "connected": True, ...}, ...],
                "available": [{"slug": ..., "connected": False, "badge_type": "configurar", ...}, ...]
            }

        """
        channels = get_stage_channels(stage_slug)
        active_connections = await self._connection_port.list_active_connections(
            tenant_id,
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
                available.append({**ch, "connected": False, "badge_type": "configurar"})
                continue

            # Check if any of the provider's channel types are connected
            if provider_types & connected_channel_types:
                # Find matching connection to include config for source attribution
                matching_conn = next(
                    (c for c in active_connections if c.channel_type in provider_types),
                    None,
                )
                conn_config = matching_conn.config if matching_conn else {}
                connected.append(
                    {**ch, "connected": True, "connection_config": conn_config},
                )
            else:
                available.append({**ch, "connected": False, "badge_type": "configurar"})

        return {"connected": connected, "available": available}
