/**
 * Maps channel slugs to their parent funnel stage slug.
 * Used by the legacy /channel/[slug] redirect and by the context
 * when it needs to construct a route-based URL for a channel.
 */
export const CHANNEL_STAGE_MAP: Record<string, string> = {
  'meta-ads': 'atraccion-captura',
  'ig-organic': 'atraccion-captura',
  'yt-organic': 'atraccion-captura',
  'google-organic': 'atraccion-captura',
  'google-ads': 'atraccion-captura',
  'facebook-organic': 'atraccion-captura',
  'email-nurture': 'nutricion-oportunidad',
  'email-launch': 'nutricion-oportunidad',
  'email-sequences': 'nutricion-oportunidad',
  'meta-retargeting': 'nutricion-oportunidad',
};

/**
 * Returns the stage slug for a given channel, falling back to 'atraccion-captura'.
 */
export function getStageForChannel(channelSlug: string): string {
  return CHANNEL_STAGE_MAP[channelSlug] ?? 'atraccion-captura';
}
