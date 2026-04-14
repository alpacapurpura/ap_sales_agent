/**
 * Maps a backend provider_name to the frontend connection page route segment.
 * Returns null for providers that don't have a dedicated connection page.
 */
const PROVIDER_ROUTE_MAP: Record<string, string> = {
  meta: "meta",
  google_analytics: "google-analytics",
  google_ads: "google-analytics",
  youtube: "youtube",
  shopify: "shopify",
  email_marketing: "mailerlite",
  manychat: "manychat",
  telegram: "telegram",
  search_console: "google-analytics",
  whatsapp: "whatsapp",
  tiktok: "tiktok",
};

export function providerToConnectionRoute(providerName: string | undefined | null): string | null {
  if (!providerName) return null;
  return PROVIDER_ROUTE_MAP[providerName] ?? null;
}
