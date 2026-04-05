import { describe, it, expect } from 'vitest';
import type { MetricValue } from '../../types/metrics';
import {
  CHANNEL_DISPLAY_REGISTRY,
  getChannelConfig,
  getSummaryMetrics,
  getPrimaryMetricSpec,
  getExpandedMetrics,
} from '../channel-display-registry';

// ─── Test data ──────────────────────────────────────────────────────────────

const igMetrics: MetricValue[] = [
  { name: 'impressions', value: 50000 },
  { name: 'reach', value: 30000 },
  { name: 'total_interactions', value: 1200 },
  { name: 'ig_followers_count', value: 8500 },
  { name: 'conversations', value: 5 },
];

const metaAdsMetrics: MetricValue[] = [
  { name: 'impressions', value: 100000 },
  { name: 'reach', value: 45000 },
  { name: 'spend', value: 250, unit: 'currency', currency: 'USD' },
  { name: 'cpc', value: 0.35, unit: 'currency', currency: 'USD' },
  { name: 'cpm', value: 5.5, unit: 'currency', currency: 'USD' },
  { name: 'meta_purchase_roas', value: 3.2 },
  { name: 'conversations', value: 10 },
];

const unknownChannelMetrics: MetricValue[] = [
  { name: 'foo', value: 100 },
  { name: 'bar', value: 200 },
  { name: 'conversations', value: 3 },
];

// ─── getChannelConfig ───────────────────────────────────────────────────────

describe('getChannelConfig', () => {
  it('returns config for known channels', () => {
    expect(getChannelConfig('ig-organic')).toBeDefined();
    expect(getChannelConfig('meta-ads')).toBeDefined();
    expect(getChannelConfig('yt-organic')).toBeDefined();
    expect(getChannelConfig('website-capture')).toBeDefined();
  });

  it('returns undefined for unknown channels', () => {
    expect(getChannelConfig('unknown-channel')).toBeUndefined();
  });
});

// ─── getSummaryMetrics ──────────────────────────────────────────────────────

describe('getSummaryMetrics', () => {
  it('filters ig-organic to only configured summary metrics', () => {
    const result = getSummaryMetrics('ig-organic', igMetrics);

    expect(result).toHaveLength(3);
    expect(result.map(m => m.name)).toEqual(['reach', 'total_interactions', 'ig_followers_count']);
  });

  it('preserves registry-defined order, not backend order', () => {
    const result = getSummaryMetrics('ig-organic', igMetrics);

    // Registry order: reach, total_interactions, ig_followers_count
    expect(result[0].name).toBe('reach');
    expect(result[1].name).toBe('total_interactions');
    expect(result[2].name).toBe('ig_followers_count');
  });

  it('filters meta-ads to configured 5 summary metrics', () => {
    const result = getSummaryMetrics('meta-ads', metaAdsMetrics);

    expect(result).toHaveLength(5);
    expect(result.map(m => m.name)).toEqual(['impressions', 'reach', 'spend', 'cpc', 'cpm']);
  });

  it('excludes conversations even for unconfigured channels', () => {
    const result = getSummaryMetrics('unknown-channel', unknownChannelMetrics);

    expect(result.map(m => m.name)).toEqual(['foo', 'bar']);
    expect(result.find(m => m.name === 'conversations')).toBeUndefined();
  });

  it('returns all metrics (minus conversations) for unknown channels', () => {
    const result = getSummaryMetrics('unknown-channel', unknownChannelMetrics);

    expect(result).toHaveLength(2);
  });

  it('omits metrics defined in config but missing from data', () => {
    const sparseMetrics: MetricValue[] = [
      { name: 'reach', value: 1000 },
      // total_interactions and ig_followers_count are missing
    ];
    const result = getSummaryMetrics('ig-organic', sparseMetrics);

    expect(result).toHaveLength(1);
    expect(result[0].name).toBe('reach');
  });

  it('returns empty array when no data matches config', () => {
    const noMatchMetrics: MetricValue[] = [
      { name: 'unrelated', value: 42 },
    ];
    const result = getSummaryMetrics('ig-organic', noMatchMetrics);

    expect(result).toHaveLength(0);
  });
});

// ─── getPrimaryMetricSpec ───────────────────────────────────────────────────

describe('getPrimaryMetricSpec', () => {
  it('returns registry primary for known channels', () => {
    expect(getPrimaryMetricSpec('ig-organic', 'organic_social'))
      .toEqual({ name: 'reach', label: 'alcance' });

    expect(getPrimaryMetricSpec('meta-ads', 'paid'))
      .toEqual({ name: 'impressions', label: 'impresiones' });

    expect(getPrimaryMetricSpec('yt-organic', 'organic_social'))
      .toEqual({ name: 'views', label: 'vistas' });

    expect(getPrimaryMetricSpec('website-capture', 'website'))
      .toEqual({ name: 'leads', label: 'leads' });
  });

  it('falls back to channelType for unknown channels', () => {
    expect(getPrimaryMetricSpec('unknown-paid', 'paid'))
      .toEqual({ name: 'impressions', label: 'impresiones' });

    expect(getPrimaryMetricSpec('unknown-organic', 'organic_social'))
      .toEqual({ name: 'reach', label: 'alcance' });

    expect(getPrimaryMetricSpec('unknown-outbound', 'outbound'))
      .toEqual({ name: 'contacts', label: 'contactos' });
  });

  it('defaults to leads for unknown channel types', () => {
    expect(getPrimaryMetricSpec('unknown', 'something_new'))
      .toEqual({ name: 'leads', label: 'leads' });
  });
});

// ─── getExpandedMetrics ─────────────────────────────────────────────────────

describe('getExpandedMetrics', () => {
  it('returns expanded specs for website-capture', () => {
    const specs = getExpandedMetrics('website-capture');

    expect(specs).toBeDefined();
    expect(specs).toHaveLength(5);
    expect(specs!.map(s => s.name)).toEqual([
      'users', 'sessions', 'engagementRate', 'bounceRate', 'avgSessionDuration',
    ]);
  });

  it('returns format hints for website metrics', () => {
    const specs = getExpandedMetrics('website-capture')!;

    expect(specs.find(s => s.name === 'engagementRate')?.format).toBe('percentage');
    expect(specs.find(s => s.name === 'bounceRate')?.format).toBe('percentage');
    expect(specs.find(s => s.name === 'avgSessionDuration')?.format).toBe('duration');
    expect(specs.find(s => s.name === 'users')?.format).toBeUndefined(); // default = number
  });

  it('returns undefined for channels without expanded config', () => {
    expect(getExpandedMetrics('ig-organic')).toBeUndefined();
    expect(getExpandedMetrics('unknown-channel')).toBeUndefined();
  });
});

// ─── Responsive visibility ──────────────────────────────────────────────────

describe('responsive field', () => {
  it('meta-ads CPC and CPM are marked responsive: sm', () => {
    const config = getChannelConfig('meta-ads')!;
    const cpc = config.summaryMetrics.find(s => s.name === 'cpc');
    const cpm = config.summaryMetrics.find(s => s.name === 'cpm');

    expect(cpc?.responsive).toBe('sm');
    expect(cpm?.responsive).toBe('sm');
  });

  it('metrics without responsive flag default to always visible', () => {
    const config = getChannelConfig('meta-ads')!;
    const impressions = config.summaryMetrics.find(s => s.name === 'impressions');
    const reach = config.summaryMetrics.find(s => s.name === 'reach');
    const spend = config.summaryMetrics.find(s => s.name === 'spend');

    expect(impressions?.responsive).toBeUndefined();
    expect(reach?.responsive).toBeUndefined();
    expect(spend?.responsive).toBeUndefined();
  });

  it('ig-organic metrics have no responsive field', () => {
    const config = getChannelConfig('ig-organic')!;

    for (const spec of config.summaryMetrics) {
      expect(spec.responsive, `${spec.name} should not have responsive`).toBeUndefined();
    }
  });
});

// ─── Registry integrity ─────────────────────────────────────────────────────

describe('CHANNEL_DISPLAY_REGISTRY integrity', () => {
  it('every entry has non-empty summaryMetrics', () => {
    for (const [slug, config] of Object.entries(CHANNEL_DISPLAY_REGISTRY)) {
      expect(config.summaryMetrics.length, `${slug} must have summaryMetrics`).toBeGreaterThan(0);
    }
  });

  it('every entry has a primaryMetric with name and label', () => {
    for (const [slug, config] of Object.entries(CHANNEL_DISPLAY_REGISTRY)) {
      expect(config.primaryMetric.name, `${slug} primaryMetric.name`).toBeTruthy();
      expect(config.primaryMetric.label, `${slug} primaryMetric.label`).toBeTruthy();
    }
  });

  it('expanded layout channels have expandedMetrics', () => {
    for (const [slug, config] of Object.entries(CHANNEL_DISPLAY_REGISTRY)) {
      if (config.layout === 'expanded') {
        expect(config.expandedMetrics, `${slug} with layout=expanded must have expandedMetrics`).toBeDefined();
        expect(config.expandedMetrics!.length).toBeGreaterThan(0);
      }
    }
  });
});
