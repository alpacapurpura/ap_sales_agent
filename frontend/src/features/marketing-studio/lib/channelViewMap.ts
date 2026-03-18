import { lazy, type LazyExoticComponent, type ComponentType } from 'react';

type LazyView = LazyExoticComponent<ComponentType<unknown>>;

const MetaView: LazyView = lazy(() =>
  import('@/features/connections/components/meta-view').then((m) => ({ default: m.MetaView }))
);

const WhatsAppView: LazyView = lazy(() =>
  import('@/features/connections/components/whatsapp-view')
);

const ShopifyView: LazyView = lazy(() =>
  import('@/features/connections/components/shopify-view').then((m) => ({ default: m.ShopifyView }))
);

const MailerLiteView: LazyView = lazy(() =>
  import('@/features/connections/components/mailerlite-view').then((m) => ({ default: m.MailerLiteView }))
);

const ManyChatView: LazyView = lazy(() =>
  import('@/features/connections/components/manychat-view').then((m) => ({ default: m.ManyChatView }))
);

const TelegramView: LazyView = lazy(() =>
  import('@/features/connections/components/telegram-view').then((m) => ({ default: m.TelegramView }))
);

const GoogleWorkspaceView: LazyView = lazy(() =>
  import('@/features/connections/components/google-workspace-view').then((m) => ({ default: m.GoogleWorkspaceView }))
);

const GoogleAnalyticsView: LazyView = lazy(() =>
  import('@/features/connections/components/google-analytics-view').then((m) => ({ default: m.GoogleAnalyticsView }))
);

const GoogleCalendarView: LazyView = lazy(() =>
  import('@/features/connections/components/google-calendar-view').then((m) => ({ default: m.GoogleCalendarView }))
);

const YoutubeView: LazyView = lazy(() =>
  import('@/features/connections/components/youtube-view').then((m) => ({ default: m.YoutubeView }))
);

/**
 * Maps channel slugs (from backend channel_registry.py) to their connection view.
 *
 * Mapping logic follows provider_name → connection view:
 *   meta        → MetaView
 *   google_analytics / google_ads → GoogleWorkspaceView (same Google OAuth)
 *   youtube     → YoutubeView
 *   whatsapp    → WhatsAppView
 *   shopify     → ShopifyView
 *   mailerlite  → MailerLiteView
 *   manychat    → ManyChatView
 *   telegram    → TelegramView
 *
 * Slugs NOT mapped (no connection view yet):
 *   tiktok-organic, tiktok-ads, tiktok-retargeting, tiktok-dm → TikTok (placeholder only)
 *   linkedin-organic → LinkedIn (no backend support)
 *   internal/manual providers → no connection needed
 */
const SLUG_TO_VIEW: Record<string, LazyView> = {
  // Meta provider
  'ig-organic': MetaView,
  'fb-organic': MetaView,
  'meta-ads': MetaView,
  'ig-dm': MetaView,
  'fb-messenger': MetaView,
  'meta-retargeting': MetaView,

  // Google Analytics provider (uses Google Workspace OAuth)
  'google-organic': GoogleWorkspaceView,
  'direct': GoogleWorkspaceView,
  'ai-search-organic': GoogleWorkspaceView,

  // Google Ads provider (uses same Google OAuth as Analytics)
  'google-ads': GoogleWorkspaceView,
  'yt-ads': GoogleWorkspaceView,
  'google-retargeting': GoogleWorkspaceView,

  // YouTube organic — connects via Google Workspace OAuth (YouTube is a sub-service there)
  'yt-organic': GoogleWorkspaceView,

  // WhatsApp provider
  'whatsapp-inbound': WhatsAppView,
  'whatsapp-outbound': WhatsAppView,
  'whatsapp': WhatsAppView,

  // Shopify provider
  'shopify': ShopifyView,
  'checkout-init': ShopifyView,
  'abandoned-cart': ShopifyView,

  // MailerLite provider
  'mailerlite': MailerLiteView,
  'mailerlite-newsletter': MailerLiteView,
  'email': MailerLiteView,

  // ManyChat provider
  'manychat': ManyChatView,
  'manychat-messenger': ManyChatView,

  // Telegram provider
  'telegram': TelegramView,

  // Google sub-services (standalone views)
  'google-workspace': GoogleWorkspaceView,
  'gmail': GoogleWorkspaceView,
  'google-analytics': GoogleAnalyticsView,
  'ga4': GoogleAnalyticsView,
  'google-calendar': GoogleCalendarView,
  'youtube': YoutubeView,
};

export function getConnectionView(slug: string): LazyView | null {
  return SLUG_TO_VIEW[slug] ?? null;
}
