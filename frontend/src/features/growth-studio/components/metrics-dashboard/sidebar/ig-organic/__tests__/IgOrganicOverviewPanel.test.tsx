import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChannelDashboardData, ChannelMetric } from '../../../../../types/metrics';

// --- Mocks ---
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue('test-token') }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: 'test-tenant' }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

const MOCK_DATA: ChannelDashboardData = {
  channelSlug: 'ig-organic',
  channelName: 'Instagram Orgánico',
  industryCategory: 'education',
  period: '30d',
  kpis: [
    { metricName: 'total_interactions', displayName: 'Interacciones', currentValue: 2450, previousValue: 2100, deltaPct: 16.7, deltaAbsolute: 350, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_views', displayName: 'Vistas', currentValue: 485000, previousValue: 410000, deltaPct: 18.3, deltaAbsolute: 75000, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_follows_and_unfollows', displayName: 'Seguidores netos', currentValue: 127, previousValue: 95, deltaPct: 33.7, deltaAbsolute: 32, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_engagement_rate', displayName: 'Engagement Rate', currentValue: 0.51, previousValue: 0.44, deltaPct: 15.9, deltaAbsolute: 0.07, unit: 'percentage', higherIsBetter: true, benchmark: { low: 0.3, median: 0.5, high: 0.8, unit: 'percentage', interpretation: 'Tasa de interacción' } },
  ],
  timeSeries: [],
  funnel: {
    steps: [
      { label: 'Vistas', metricName: 'ig_views', value: 485000, conversionRate: null },
      { label: 'Interacciones', metricName: 'total_interactions', value: 2450, conversionRate: 0.51 },
    ],
  },
  frequencyAlert: null,
};

vi.mock('../../../../../hooks/useChannelDashboard', () => ({
  useChannelDashboard: () => ({ data: MOCK_DATA, isLoading: false }),
}));

vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

import { IgOrganicOverviewPanel } from '../IgOrganicOverviewPanel';

const CHANNEL: ChannelMetric = {
  slug: 'ig-organic',
  name: 'Instagram Orgánico',
  channelType: 'organic_social',
  metrics: [],
  sourceLabel: 'Instagram',
  connected: true,
};

describe('IgOrganicOverviewPanel', () => {
  it('renders the channel name in the header', () => {
    render(<IgOrganicOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByText('Instagram Orgánico')).toBeInTheDocument();
  });

  it('renders KPI display names', () => {
    render(<IgOrganicOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    // "Interacciones" and "Vistas" appear both in KPIs and funnel
    expect(screen.getAllByText('Interacciones').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Vistas').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument();
  });

  it('renders the funnel section', () => {
    render(<IgOrganicOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByText('Funnel de Conversión')).toBeInTheDocument();
  });

  it('renders the "Dashboard completo" button when onExpand is provided', () => {
    render(<IgOrganicOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByLabelText('Dashboard completo')).toBeInTheDocument();
  });
});
