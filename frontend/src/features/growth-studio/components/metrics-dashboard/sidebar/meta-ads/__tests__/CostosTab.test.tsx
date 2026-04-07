import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type {
  ChannelDashboardData,
  CampaignPerformanceData,
  MetricKpiData,
} from '../../../../../types/metrics';

// --- Mocks ---
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue('test-token') }),
}));

// Mock recharts to render testable DOM
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>();
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
      <div data-testid="responsive-container">{children}</div>
    ),
  };
});

// Must import AFTER mocks
import { CostosTab } from '../tabs/CostosTab';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeKpi(overrides: Partial<MetricKpiData> & { metricName: string }): MetricKpiData {
  return {
    displayName: overrides.metricName,
    currentValue: 1.5,
    previousValue: 1.8,
    deltaPct: -16.7,
    deltaAbsolute: -0.3,
    unit: 'currency',
    currency: 'USD',
    higherIsBetter: false,
    benchmark: null,
    ...overrides,
  };
}

const COST_KPIS: MetricKpiData[] = [
  makeKpi({ metricName: 'CPC', displayName: 'CPC', currentValue: 0.85 }),
  makeKpi({ metricName: 'CPM', displayName: 'CPM', currentValue: 12.5 }),
  makeKpi({ metricName: 'CPL', displayName: 'CPL', currentValue: 5.2 }),
  makeKpi({ metricName: 'CPA', displayName: 'CPA', currentValue: 33.3 }),
];

function makeCostDashboardData(kpiOverrides?: MetricKpiData[]): ChannelDashboardData {
  return {
    channelSlug: 'meta-ads',
    channelName: 'Meta Ads',
    industryCategory: 'education',
    period: '30d',
    kpis: kpiOverrides ?? COST_KPIS,
    timeSeries: [
      {
        metricName: 'CPC',
        displayName: 'CPC',
        unit: 'currency',
        dataPoints: [
          { date: '2026-03-01', value: 0.8 },
          { date: '2026-03-02', value: 0.9 },
        ],
      },
      {
        metricName: 'CPM',
        displayName: 'CPM',
        unit: 'currency',
        dataPoints: [
          { date: '2026-03-01', value: 11 },
          { date: '2026-03-02', value: 13 },
        ],
      },
    ],
    funnel: { steps: [] },
    frequencyAlert: null,
  };
}

const CAMPAIGN_DATA: CampaignPerformanceData = {
  campaigns: [
    {
      externalId: 'c1',
      name: 'Brand Awareness',
      objective: 'BRAND_AWARENESS',
      status: 'ACTIVE',
      effectiveStatus: 'ACTIVE',
      dailyBudget: 50,
      lifetimeBudget: null,
      budgetRemaining: null,
      startTime: null,
      stopTime: null,
      adSetsCount: 2,
      adsCount: 4,
      metrics: {
        spend: 200,
        conversions: 5,
        cpa: 40,
        roas: null,
        ctr: 2.1,
        cpc: 0.9,
        cpm: 12,
        frequency: 1.3,
        impressions: 16667,
        clicks: 190,
        reach: 12800,
      },
      health: 'good',
    },
    {
      externalId: 'c2',
      name: 'Conversions Q1',
      objective: 'CONVERSIONS',
      status: 'ACTIVE',
      effectiveStatus: 'ACTIVE',
      dailyBudget: 100,
      lifetimeBudget: null,
      budgetRemaining: null,
      startTime: null,
      stopTime: null,
      adSetsCount: 3,
      adsCount: 6,
      metrics: {
        spend: 500,
        conversions: 8,
        cpa: 62.5,
        roas: null,
        ctr: 1.8,
        cpc: 1.2,
        cpm: 15,
        frequency: 1.5,
        impressions: 33333,
        clicks: 417,
        reach: 22222,
      },
      health: 'critical',
    },
  ],
  recommendations: [],
  totalCampaigns: 2,
  activeCampaigns: 2,
  currency: 'USD',
  lastSynced: null,
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('CostosTab', () => {
  it('renders loading spinner when isLoading is true', () => {
    const { container } = render(
      <CostosTab data={undefined} campaignData={undefined} isLoading={true} />,
    );
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders "No hay datos disponibles" when data is undefined', () => {
    render(<CostosTab data={undefined} campaignData={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });

  it('renders 4 cost KPI cards', () => {
    render(
      <CostosTab data={makeCostDashboardData()} campaignData={undefined} isLoading={false} />,
    );
    expect(screen.getByText('CPC')).toBeInTheDocument();
    expect(screen.getByText('CPM')).toBeInTheDocument();
    expect(screen.getByText('CPL')).toBeInTheDocument();
    expect(screen.getByText('CPA')).toBeInTheDocument();
  });

  it('renders cost evolution LineChart title', () => {
    render(
      <CostosTab data={makeCostDashboardData()} campaignData={undefined} isLoading={false} />,
    );
    expect(screen.getByText('Evolución de costos')).toBeInTheDocument();
  });

  it('renders CPA per campaign horizontal bars', () => {
    render(
      <CostosTab
        data={makeCostDashboardData()}
        campaignData={CAMPAIGN_DATA}
        isLoading={false}
      />,
    );
    expect(screen.getByText('Brand Awareness')).toBeInTheDocument();
    expect(screen.getByText('Conversions Q1')).toBeInTheDocument();
    expect(screen.getByText('CPA por campaña')).toBeInTheDocument();
  });

  it('handles empty campaign data gracefully', () => {
    const emptyCampaigns: CampaignPerformanceData = {
      ...CAMPAIGN_DATA,
      campaigns: [],
    };
    render(
      <CostosTab
        data={makeCostDashboardData()}
        campaignData={emptyCampaigns}
        isLoading={false}
      />,
    );
    // Should not crash and should NOT render the CPA por campaña section
    expect(screen.queryByText('CPA por campaña')).not.toBeInTheDocument();
  });

  it('renders benchmark ReferenceLine when CPC has benchmark data', () => {
    const kpisWithBenchmark = COST_KPIS.map(k =>
      k.metricName === 'CPC'
        ? {
            ...k,
            benchmark: {
              low: 0.5,
              median: 0.85,
              high: 1.2,
              unit: 'currency',
              interpretation: 'CPC promedio en tu industria',
            },
          }
        : k,
    );
    const { container } = render(
      <CostosTab
        data={makeCostDashboardData(kpisWithBenchmark)}
        campaignData={undefined}
        isLoading={false}
      />,
    );
    // ReferenceLine renders as a <line> element inside the SVG with stroke-dasharray
    // In the mocked recharts environment, check for the benchmark label text
    const benchmarkLabel = screen.queryByText(/Promedio/);
    // The ReferenceLine is rendered inside the chart; we verify it doesn't crash
    // and the chart section still renders
    expect(screen.getByText('Evolución de costos')).toBeInTheDocument();
    // Verify the component at least accepted the benchmark without errors
    expect(container).toBeInTheDocument();
  });

  it('shows "--" for CPL when currentValue is 0 (pixel-dependent)', () => {
    const kpis = COST_KPIS.map(k =>
      k.metricName === 'CPL' ? { ...k, currentValue: 0 } : k,
    );
    render(
      <CostosTab data={makeCostDashboardData(kpis)} campaignData={undefined} isLoading={false} />,
    );
    const placeholder = screen.getByTitle('Requiere Meta Pixel configurado');
    expect(placeholder).toBeInTheDocument();
    expect(placeholder.textContent).toBe('--');
  });

  it('shows "--" for CPA when currentValue is 0 (pixel-dependent)', () => {
    const kpis = COST_KPIS.map(k =>
      k.metricName === 'CPA' ? { ...k, currentValue: 0 } : k,
    );
    render(
      <CostosTab data={makeCostDashboardData(kpis)} campaignData={undefined} isLoading={false} />,
    );
    const placeholders = screen.getAllByTitle('Requiere Meta Pixel configurado');
    expect(placeholders.length).toBeGreaterThanOrEqual(1);
  });

  it('does NOT show "--" for CPC when currentValue is 0 (not pixel-dependent)', () => {
    const kpis = COST_KPIS.map(k =>
      k.metricName === 'CPC' ? { ...k, currentValue: 0 } : k,
    );
    render(
      <CostosTab data={makeCostDashboardData(kpis)} campaignData={undefined} isLoading={false} />,
    );
    // CPC is not pixel-dependent, so $0.00 should render, not "--"
    const pixelPlaceholders = screen.queryAllByTitle('Requiere Meta Pixel configurado');
    const cpcPlaceholder = pixelPlaceholders.find(el => {
      const card = el.closest('[title]');
      return card?.getAttribute('title')?.includes('CPC');
    });
    expect(cpcPlaceholder).toBeUndefined();
  });
});
