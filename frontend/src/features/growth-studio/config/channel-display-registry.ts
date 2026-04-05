import type { MetricValue } from '../types/metrics';

// ─── Types ──────────────────────────────────────────────────────────────────

export type MetricFormat = 'number' | 'currency' | 'percentage' | 'duration';

/** Specification of a metric for display in compact row or expanded grid. */
export interface MetricDisplaySpec {
  /** Metric name as sent by the backend (MetricValue.name). */
  name: string;
  /** Label override (fallback: catalog -> METRIC_LABELS -> raw name). */
  label?: string;
  /** Format hint (auto-detected from unit if omitted). */
  format?: MetricFormat;
  /** Responsive visibility: 'always' (default) or 'sm' (hidden below 640px). */
  responsive?: 'always' | 'sm';
}

/** Display configuration for a specific channel. */
export interface ChannelDisplayConfig {
  /** Metrics to show in the compact row view (top 3-5). */
  summaryMetrics: MetricDisplaySpec[];
  /** Primary metric for card view in ChannelGroup. */
  primaryMetric: { name: string; label: string };
  /** Layout hint: 'row' = inline pills (default), 'expanded' = grid. */
  layout?: 'row' | 'expanded';
  /** Metrics for the expanded grid view (only when layout='expanded'). */
  expandedMetrics?: MetricDisplaySpec[];
}

// ─── Registry (single source of truth) ──────────────────────────────────────

export const CHANNEL_DISPLAY_REGISTRY: Record<string, ChannelDisplayConfig> = {
  'ig-organic': {
    summaryMetrics: [
      { name: 'reach', label: 'Alcance' },
      { name: 'total_interactions', label: 'Interacciones' },
      { name: 'ig_followers_count', label: 'Seguidores' },
    ],
    primaryMetric: { name: 'reach', label: 'alcance' },
  },
  'meta-ads': {
    summaryMetrics: [
      { name: 'impressions', label: 'Impresiones' },
      { name: 'reach', label: 'Alcance' },
      { name: 'spend', label: 'Inversión', format: 'currency' },
      { name: 'cpc', label: 'CPC', format: 'currency', responsive: 'sm' },
      { name: 'cpm', label: 'CPM', format: 'currency', responsive: 'sm' },
    ],
    primaryMetric: { name: 'impressions', label: 'impresiones' },
  },
  'yt-organic': {
    summaryMetrics: [
      { name: 'views', label: 'Vistas' },
      { name: 'engagement', label: 'Engagement' },
      { name: 'subscribers_gained', label: 'Suscriptores' },
    ],
    primaryMetric: { name: 'views', label: 'vistas' },
  },
  'website-capture': {
    summaryMetrics: [
      { name: 'visitors' },
    ],
    primaryMetric: { name: 'leads', label: 'leads' },
    layout: 'expanded',
    expandedMetrics: [
      { name: 'users', label: 'Visitantes' },
      { name: 'sessions', label: 'Sesiones' },
      { name: 'engagementRate', label: 'Engagement', format: 'percentage' },
      { name: 'bounceRate', label: 'Bounce', format: 'percentage' },
      { name: 'avgSessionDuration', label: 'Duracion', format: 'duration' },
    ],
  },
};

// ─── Accessor functions (pure, testable) ────────────────────────────────────

/** Get the display config for a channel, or undefined for fallback. */
export function getChannelConfig(slug: string): ChannelDisplayConfig | undefined {
  return CHANNEL_DISPLAY_REGISTRY[slug];
}

/**
 * Filter metrics for the compact row view.
 * Channels with config -> only summaryMetrics in defined order.
 * Channels without config -> all metrics (excluding conversations).
 */
export function getSummaryMetrics(slug: string, allMetrics: MetricValue[]): MetricValue[] {
  const config = CHANNEL_DISPLAY_REGISTRY[slug];
  const filtered = allMetrics.filter(m => m.name !== 'conversations');

  if (!config) return filtered;

  const specNames = config.summaryMetrics.map(s => s.name);
  return specNames
    .map(name => filtered.find(m => m.name === name))
    .filter((m): m is MetricValue => m !== undefined);
}

/**
 * Get the primary metric spec for card view.
 * Channels with config -> registry value.
 * Channels without config -> fallback by channelType.
 */
export function getPrimaryMetricSpec(
  slug: string,
  channelType: string,
): { name: string; label: string } {
  const config = CHANNEL_DISPLAY_REGISTRY[slug];
  if (config) return config.primaryMetric;

  switch (channelType) {
    case 'paid':
    case 'retargeting':
      return { name: 'impressions', label: 'impresiones' };
    case 'organic_social':
    case 'organic':
      return { name: 'reach', label: 'alcance' };
    case 'outbound':
      return { name: 'contacts', label: 'contactos' };
    default:
      return { name: 'leads', label: 'leads' };
  }
}

/** Get expanded metrics config for grid layout, if defined. */
export function getExpandedMetrics(slug: string): MetricDisplaySpec[] | undefined {
  return CHANNEL_DISPLAY_REGISTRY[slug]?.expandedMetrics;
}
