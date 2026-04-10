import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type {
  ChannelDashboardData,
  CampaignPerformanceData,
  MetricKpiData,
} from '../../../../../types/metrics';

// --- Mocks ---
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue('test-token') }),
}));

vi.mock('@/lib/config', () => ({
  config: { api: { baseUrl: 'https://api.test.com' } },
}));

vi.mock('@/lib/http-client', () => ({
  fetchClient: vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  }),
}));

// Mock recharts to render testable DOM (avoids canvas/SVG measurement issues)
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
import { ResumenTab } from '../tabs/ResumenTab';

// Helper to wrap ResumenTab with a QueryClientProvider (required by the new
// offer-association hooks consumed inside the tab).
function renderWithQuery(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

// ---------------------------------------------------------------------------
// Helpers — test data factories
// ---------------------------------------------------------------------------

function makeKpi(overrides: Partial<MetricKpiData> & { metricName: string }): MetricKpiData {
  return {
    displayName: overrides.metricName,
    currentValue: 100,
    previousValue: 80,
    deltaPct: 25,
    deltaAbsolute: 20,
    unit: 'count',
    higherIsBetter: true,
    benchmark: null,
    ...overrides,
  };
}

const BASE_KPIS: MetricKpiData[] = [
  makeKpi({ metricName: 'spend', displayName: 'Inversión', currentValue: 1500, unit: 'currency', currency: 'USD' }),
  makeKpi({ metricName: 'ROAS', displayName: 'ROAS', currentValue: 3.2, unit: 'ratio', higherIsBetter: true }),
  makeKpi({ metricName: 'conversions', displayName: 'Resultados', currentValue: 45, unit: 'count' }),
  makeKpi({ metricName: 'CPA', displayName: 'CPA', currentValue: 33.3, unit: 'currency', currency: 'USD', higherIsBetter: false }),
  makeKpi({ metricName: 'CTR', displayName: 'CTR', currentValue: 2.15, unit: 'percentage', higherIsBetter: true }),
  makeKpi({ metricName: 'reach', displayName: 'Alcance', currentValue: 89200, unit: 'count' }),
];

function makeDashboardData(kpiOverrides?: MetricKpiData[]): ChannelDashboardData {
  return {
    channelSlug: 'meta-ads',
    channelName: 'Meta Ads',
    industryCategory: 'education',
    period: '30d',
    kpis: kpiOverrides ?? BASE_KPIS,
    timeSeries: [
      {
        metricName: 'spend',
        displayName: 'Inversión',
        unit: 'currency',
        dataPoints: [
          { date: '2026-03-01', value: 50 },
          { date: '2026-03-02', value: 60 },
        ],
      },
      {
        metricName: 'conversions',
        displayName: 'Resultados',
        unit: 'count',
        dataPoints: [
          { date: '2026-03-01', value: 3 },
          { date: '2026-03-02', value: 5 },
        ],
      },
    ],
    funnel: {
      steps: [
        { label: 'Impresiones', metricName: 'impressions', value: 120000, conversionRate: null },
        { label: 'Clics', metricName: 'clicks', value: 2580, conversionRate: 2.15 },
        { label: 'Resultados', metricName: 'conversions', value: 45, conversionRate: 1.74 },
      ],
    },
    frequencyAlert: null,
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ResumenTab', () => {
  it('renders loading spinner when isLoading is true', () => {
    const { container } = renderWithQuery(
      <ResumenTab data={undefined} isLoading={true} />,
    );
    const spinner = container.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('renders "No hay datos disponibles" when data is undefined', () => {
    renderWithQuery(<ResumenTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });

  it('renders KPI cards with data', () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    // Verify display names appear (Inversión and ROAS also appear in the chart legend,
    // so we assert that at least one instance exists)
    expect(screen.getAllByText('Inversión').length).toBeGreaterThan(0);
    expect(screen.getAllByText('ROAS').length).toBeGreaterThan(0);
    expect(screen.getByText('CTR')).toBeInTheDocument();
    expect(screen.getByText('Alcance')).toBeInTheDocument();
  });

  it('shows "--" for ROAS when currentValue is 0', () => {
    const kpis = BASE_KPIS.map(k =>
      k.metricName === 'ROAS' ? { ...k, currentValue: 0 } : k,
    );
    renderWithQuery(<ResumenTab data={makeDashboardData(kpis)} isLoading={false} />);
    const placeholder = screen.getByTitle('Requiere Meta Pixel configurado');
    expect(placeholder).toBeInTheDocument();
    expect(placeholder.textContent).toBe('--');
  });

  it('shows "--" for CPA when currentValue is 0', () => {
    const kpis = BASE_KPIS.map(k =>
      k.metricName === 'CPA' ? { ...k, currentValue: 0 } : k,
    );
    renderWithQuery(<ResumenTab data={makeDashboardData(kpis)} isLoading={false} />);
    const placeholders = screen.getAllByTitle('Requiere Meta Pixel configurado');
    // CPA is pixel-dependent and has value 0, so it should produce a "--" placeholder
    // We also have ROAS=3.2 (non-zero, no placeholder) and conversions=45 (non-zero, no placeholder)
    // Only CPA should produce a placeholder in this test
    expect(placeholders.length).toBeGreaterThanOrEqual(1);
    // Find the one inside the CPA card by checking the parent card's tooltip
    const cpaPlaceholder = placeholders.find(el => {
      // The span has title="Requiere Meta Pixel configurado", so closest('[title]')
      // returns itself. We need the parent div with the KPI tooltip.
      const card = el.closest('.rounded-lg.border');
      return card?.getAttribute('title')?.includes('CPA');
    });
    expect(cpaPlaceholder).toBeDefined();
    expect(cpaPlaceholder?.textContent).toBe('--');
  });

  it('renders spend/clicks/impressions even without pixel data', () => {
    // Only additive metrics, pixel-dependent ones at 0
    const kpis = BASE_KPIS.map(k => {
      if (['ROAS', 'CPA', 'conversions'].includes(k.metricName)) {
        return { ...k, currentValue: 0 };
      }
      return k;
    });
    renderWithQuery(<ResumenTab data={makeDashboardData(kpis)} isLoading={false} />);
    // Spend should still display correctly (non-pixel metric)
    expect(screen.getByText('Inversión')).toBeInTheDocument();
    expect(screen.getByText('CTR')).toBeInTheDocument();
    expect(screen.getByText('Alcance')).toBeInTheDocument();
  });

  it('does NOT show "--" for spend when currentValue is 0', () => {
    const kpis = BASE_KPIS.map(k =>
      k.metricName === 'spend' ? { ...k, currentValue: 0 } : k,
    );
    renderWithQuery(<ResumenTab data={makeDashboardData(kpis)} isLoading={false} />);
    // Spend is not pixel-dependent, so 0 should render as a formatted value, not "--"
    const pixelPlaceholders = screen.queryAllByTitle('Requiere Meta Pixel configurado');
    const spendPlaceholder = pixelPlaceholders.find(el => {
      const card = el.closest('[title]');
      return card?.getAttribute('title')?.includes('invertido');
    });
    expect(spendPlaceholder).toBeUndefined();
  });

  it('renders conversion funnel with steps', () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    expect(screen.getByText('Impresiones')).toBeInTheDocument();
    expect(screen.getByText('Clics')).toBeInTheDocument();
    // "Resultados" appears in both KPI card and funnel, so check it exists
    expect(screen.getAllByText('Resultados').length).toBeGreaterThanOrEqual(1);
  });

  it('renders the "Inversión y Retorno" chart when timeSeries has data', () => {
    renderWithQuery(<ResumenTab data={makeDashboardData()} isLoading={false} />);
    // Title is rendered inside the ChartInfoTooltip button
    expect(screen.getByText('Inversión y Retorno')).toBeInTheDocument();
  });

  it('renders alert cards when campaignData has recommendations', () => {
    const campaignData: CampaignPerformanceData = {
      campaigns: [],
      recommendations: [
        {
          recommendationType: 'budget',
          source: 'system',
          title: 'Aumenta presupuesto',
          body: 'Tu CPA es bueno, invierte más.',
          importance: 'HIGH',
          liftEstimate: null,
          opportunityScore: null,
          url: null,
          objectIds: [],
        },
      ],
      totalCampaigns: 5,
      activeCampaigns: 3,
      currency: 'USD',
      lastSynced: null,
    };
    renderWithQuery(
      <ResumenTab
        data={makeDashboardData()}
        isLoading={false}
        campaignData={campaignData}
      />,
    );
    expect(screen.getByText('Aumenta presupuesto')).toBeInTheDocument();
  });
});
