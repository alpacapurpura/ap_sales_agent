/** Semantic colors per channel slug for Recharts visualizations. */
export const CHANNEL_COLORS: Record<string, string> = {
  'meta-ads': '#1877F2',
  'ig-organic': '#E4405F',
  'fb-organic': '#1877F2',
  'google-ads': '#EA4335',
  'google-organic': '#34A853',
  'yt-organic': '#FF0000',
  'yt-ads': '#FF0000',
  'tiktok-organic': '#00F2EA',
  'tiktok-ads': '#00F2EA',
  'direct': '#6B7280',
  'ai-search-organic': '#8B5CF6',
  'manychat-comments': '#0084FF',
  'linkedin-organic': '#0A66C2',
  'email-capture': '#F59E0B',
  'cold-contact': '#6B7280',
};

/** Fallback color for unknown channels. */
export const DEFAULT_CHANNEL_COLOR = '#6B7280';

/** Get color for a channel slug, with fallback. */
export function getChannelColor(slug: string): string {
  return CHANNEL_COLORS[slug] ?? DEFAULT_CHANNEL_COLOR;
}
