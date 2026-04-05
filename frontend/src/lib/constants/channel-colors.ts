/**
 * Canonical channel color palette — single source of truth.
 *
 * Each platform occupies an exclusive hue zone so channels are always
 * visually distinguishable in charts. Organic/ads/DM variants use
 * lighter or darker shades within the same family.
 */

export const CHANNEL_COLORS: Record<string, string> = {
  // ── Instagram (pink / purple-pink) ──────────────────────────────────
  'ig-organic': '#E1306C',
  'ig-dm': '#C13584',

  // ── Facebook (blue) ─────────────────────────────────────────────────
  'fb-organic': '#1877F2',
  'fb-messenger': '#0099FF',

  // ── YouTube (red) ───────────────────────────────────────────────────
  'yt-organic': '#FF0000',
  'yt-ads': '#CC0000',

  // ── TikTok (teal) ──────────────────────────────────────────────────
  'tiktok-organic': '#00C9C8',
  'tiktok-ads': '#00A3A2',
  'tiktok-dm': '#00E5E4',

  // ── Meta Ads (indigo) ──────────────────────────────────────────────
  'meta-ads': '#5B5FC7',
  'meta-retargeting': '#7B61FF',

  // ── Google (official brand colors) ─────────────────────────────────
  'google-ads': '#EA4335',
  'google-retargeting': '#D93025',
  'google-organic': '#34A853',
  'search-console': '#1B8A3E',

  // ── AI Search ──────────────────────────────────────────────────────
  'ai-search-organic': '#8B5CF6',

  // ── Direct traffic ─────────────────────────────────────────────────
  'direct': '#78716C',

  // ── LinkedIn ───────────────────────────────────────────────────────
  'linkedin-organic': '#0A66C2',

  // ── WhatsApp ───────────────────────────────────────────────────────
  'whatsapp': '#25D366',

  // ── ManyChat (violet — variants rarely coexist) ────────────────────
  'manychat': '#7C3AED',
  'manychat-messenger': '#7C3AED',
  'manychat-ig': '#7C3AED',
  'manychat-wa': '#7C3AED',
  'manychat-sequences': '#7C3AED',
  'manychat-bofu': '#7C3AED',
  'manychat-comments': '#7C3AED',

  // ── Email (amber — variants rarely coexist) ────────────────────────
  'email-capture': '#F59E0B',
  'email-newsletter': '#F59E0B',
  'email-sequence': '#F59E0B',

  // ── Shopify (lime) ─────────────────────────────────────────────────
  'shopify': '#96BF48',
  'shopify-checkout': '#7EA838',
  'abandoned-cart': '#D97706',

  // ── Website family (sky) ───────────────────────────────────────────
  'website-total': '#0EA5E9',
  'website-overview': '#0EA5E9',
  'website-capture': '#0284C7',
  'meta-pixel': '#38BDF8',

  // ── Landing pages (cyan) ───────────────────────────────────────────
  'landing-form': '#06B6D4',
  'landing': '#06B6D4',

  // ── AI SDR / AI Agent (indigo 500) ─────────────────────────────────
  'ai-sdr': '#6366F1',
  'ai-agent': '#6366F1',

  // ── Cold contact (stone) ───────────────────────────────────────────
  'cold-contact': '#A8A29E',

  // ── Meeting / payment / checkout (teal + orange) ───────────────────
  'meeting-booked': '#14B8A6',
  'link-enviado': '#F97316',
  'checkout-lp': '#FB923C',
};

/** Fallback color for unknown channels. */
export const DEFAULT_CHANNEL_COLOR = '#6B7280';

/**
 * Get the brand color for a channel slug.
 *
 * Resolution order:
 *  1. Exact match in CHANNEL_COLORS
 *  2. Prefix match (e.g. `email-*`, `manychat-*`, `shopify-*`)
 *  3. DEFAULT_CHANNEL_COLOR
 */
export function getChannelColor(slug: string): string {
  const key = slug.toLowerCase();

  // Exact match
  if (key in CHANNEL_COLORS) return CHANNEL_COLORS[key];

  // Prefix matching for families that share a single color
  if (key.startsWith('email-')) return '#F59E0B';
  if (key.startsWith('manychat-')) return '#7C3AED';
  if (key.startsWith('shopify-')) return '#96BF48';
  if (key.startsWith('tiktok-')) return '#00C9C8';
  if (key.startsWith('whatsapp-')) return '#25D366';

  return DEFAULT_CHANNEL_COLOR;
}
