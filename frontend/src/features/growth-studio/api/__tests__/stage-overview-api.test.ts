import { describe, it, expect, vi, beforeEach } from 'vitest';

// ── Mocks ──────────────────────────────────────────────────────────────────────

const mockFetch = vi.fn();

vi.mock('@/lib/http-client', () => ({
  fetchClient: (...args: unknown[]) => mockFetch(...args),
}));

vi.mock('@/lib/config', () => ({
  config: {
    api: { baseUrl: 'http://localhost:8000' },
  },
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { stageOverviewApi } from '../stage-overview-api';

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('stageOverviewApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls the correct URL for attraction overview', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        stage: 'attraction',
        header_kpis: { reach: 1000 },
        groups: [],
        channel_list: [],
        bottlenecks: [],
        period: 'last_30_days',
      }),
    });

    await stageOverviewApi.getStageOverview('token', 'attraction');

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/analytics/metrics/attraction/overview',
      expect.objectContaining({
        headers: { Authorization: 'Bearer token' },
      }),
    );
  });

  it('maps snake_case response to camelCase', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        stage: 'attraction',
        header_kpis: { reach: 5000 },
        mini_funnel: {
          source_label: 'Visitantes',
          source_value: 10000,
          target_label: 'Leads',
          target_value: 500,
          conversion_rate: 5.0,
        },
        groups: [
          { group_key: 'paid', group_label: 'Paid', channel_count: 2 },
        ],
        channel_list: [
          {
            slug: 'meta-ads',
            name: 'Meta Ads',
            channel_type: 'paid',
            group_key: 'paid',
            connected: true,
            headline_kpi: { name: 'spend', value: 1500, unit: 'currency' },
            last_updated: '2026-04-06T12:00:00Z',
            stale: false,
            provider_name: 'meta',
          },
        ],
        bottlenecks: [
          { type: 'low_conversion', metric_label: 'Conv. Rate', severity: 'warning' },
        ],
        period: 'last_30_days',
        last_updated: '2026-04-06T12:00:00Z',
      }),
    });

    const result = await stageOverviewApi.getStageOverview('token', 'attraction');

    // Verify camelCase mapping
    expect(result.headerKpis).toEqual({ reach: 5000 });
    expect(result.miniFunnel?.sourceLabel).toBe('Visitantes');
    expect(result.miniFunnel?.conversionRate).toBe(5.0);
    expect(result.groups[0].groupKey).toBe('paid');
    expect(result.groups[0].groupLabel).toBe('Paid');
    expect(result.channelList[0].channelType).toBe('paid');
    expect(result.channelList[0].groupKey).toBe('paid');
    expect(result.channelList[0].headlineKpi?.name).toBe('spend');
    expect(result.channelList[0].providerName).toBe('meta');
    expect(result.bottlenecks[0].metricLabel).toBe('Conv. Rate');
    expect(result.lastUpdated).toBe('2026-04-06T12:00:00Z');
  });

  it('appends period param when not last_30_days', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        stage: 'sales',
        header_kpis: {},
        groups: [],
        channel_list: [],
        bottlenecks: [],
        period: 'weekly',
      }),
    });

    await stageOverviewApi.getStageOverview('token', 'sales', 'weekly');

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/analytics/metrics/sales/overview?period=weekly',
      expect.any(Object),
    );
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(
      stageOverviewApi.getStageOverview('token', 'attraction'),
    ).rejects.toThrow('Stage overview API returned 500');
  });
});
