export type ChannelCategory = 'active' | 'disconnected' | 'no-data' | 'proximamente';

interface ClassifiableChannel {
  connected: boolean;
  slug: string;
  metrics: { value: number }[];
}

/**
 * Classify a channel into one of four display categories.
 * Extracted from ChannelRow rendering logic for reuse in LazyChannelGroup.
 */
export function classifyChannel(channel: ClassifiableChannel): ChannelCategory {
  if (!channel.connected) return 'disconnected';

  const hasEmptyOrZeroMetrics =
    channel.metrics.length === 0 || channel.metrics.every(m => m.value === 0);

  // "Próximamente" slugs — features not yet built
  if (
    (channel.slug === 'ai-sdr' && hasEmptyOrZeroMetrics) ||
    channel.slug === 'checkout-lp' ||
    (channel.slug === 'link-enviado' && channel.metrics.length === 0)
  ) {
    return 'proximamente';
  }

  if (hasEmptyOrZeroMetrics) return 'no-data';

  return 'active';
}
