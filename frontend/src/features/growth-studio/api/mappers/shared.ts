import type { ChannelMetric, MetricValue, TrafficGroup } from "../../types/metrics";

/** Shape of a raw metric item from the API before field-name mapping. */
export interface RawMetric {
  name: string;
  value: number;
  unit?: string;
  currency?: string;
  breakdown?: Record<string, number>;
}

/** Shape of a raw channel item from the API before field-name mapping. */
export interface RawChannel {
  slug: string;
  name: string;
  channel_type: string;
  metrics?: RawMetric[];
  source_label: string;
  connected: boolean;
  provider_name?: string;
  source_display_name?: string;
  cost_type?: string;
  last_updated?: string;
  stale?: boolean;
  error_message?: string;
  value?: number;
}

/** Shape of a raw group item from the API before field-name mapping. */
export interface RawGroup {
  totals?: Record<string, number>;
  channels?: RawChannel[];
}

export function mapMetric(raw: RawMetric): MetricValue {
  return {
    name: raw.name,
    value: raw.value,
    unit: raw.unit ?? undefined,
    currency: raw.currency ?? undefined,
    breakdown: raw.breakdown ?? undefined,
  };
}

export function mapChannel(raw: RawChannel): ChannelMetric {
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

export function mapGroup(raw: RawGroup): TrafficGroup {
  return {
    totals: raw.totals ?? {},
    channels: (raw.channels ?? []).map(mapChannel),
  };
}
