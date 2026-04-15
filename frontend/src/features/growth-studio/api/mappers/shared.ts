import type { ChannelMetric, MetricValue } from "../../types/metrics";

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Raw API response mapper
export function mapMetric(raw: any): MetricValue {
  return {
    name: raw.name,
    value: raw.value,
    unit: raw.unit ?? undefined,
    currency: raw.currency ?? undefined,
    breakdown: raw.breakdown ?? undefined,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Raw API response mapper
export function mapChannel(raw: any): ChannelMetric {
  return {
    slug: raw.slug,
    name: raw.name,
    channelType: raw.channel_type,
    metrics: (raw.metrics ?? []).map(mapMetric),
    sourceLabel: raw.source_label,
    connected: raw.connected,
    providerName: raw.provider_name ?? undefined,
    sourceDisplayName: raw.source_display_name ?? undefined,
    costType: raw.cost_type ?? undefined,
    lastUpdated: raw.last_updated ?? undefined,
    stale: raw.stale ?? false,
    errorMessage: raw.error_message ?? undefined,
    value: raw.value ?? undefined,
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any -- Raw API response mapper
export function mapGroup(raw: any) {
  return {
    totals: raw.totals ?? {},
    channels: (raw.channels ?? []).map(mapChannel),
  };
}
