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
  channelSlug: 'yt-organic',
  channelName: 'YouTube Org\u00e1nico',
  industryCategory: 'education',
  period: '30d',
  kpis: [
    { metricName: 'views', displayName: 'Vistas', currentValue: 125000, previousValue: 100000, deltaPct: 25.0, deltaAbsolute: 25000, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'watch_time_minutes', displayName: 'Minutos Vistos', currentValue: 8500, previousValue: 7200, deltaPct: 18.1, deltaAbsolute: 1300, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'subscribers_gained', displayName: 'Suscriptores Ganados', currentValue: 340, previousValue: 280, deltaPct: 21.4, deltaAbsolute: 60, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'avg_view_percentage', displayName: '% Retenci\u00f3n Promedio', currentValue: 52.3, previousValue: 48.1, deltaPct: 8.7, deltaAbsolute: 4.2, unit: 'percentage', higherIsBetter: true, benchmark: { low: 30, median: 50, high: 70, unit: 'percentage', interpretation: 'Porcentaje promedio de retenci\u00f3n' } },
    { metricName: 'subscribers_lost', displayName: 'Suscriptores Perdidos', currentValue: 45, previousValue: 40, deltaPct: 12.5, deltaAbsolute: 5, unit: 'count', higherIsBetter: false, benchmark: null },
  ],
  timeSeries: [],
  funnel: {
    steps: [
      { label: 'Vistas', metricName: 'views', value: 125000, conversionRate: null },
      { label: 'Engagement', metricName: 'engagement', value: 4500, conversionRate: 3.6 },
      { label: 'Suscriptores', metricName: 'subscribers_gained', value: 340, conversionRate: 7.6 },
      { label: 'Clics Tarjetas', metricName: 'card_clicks', value: 120, conversionRate: 35.3 },
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

import { YouTubeOverviewPanel } from '../YouTubeOverviewPanel';

const CHANNEL: ChannelMetric = {
  slug: 'yt-organic',
  name: 'YouTube Org\u00e1nico',
  channelType: 'organic_social',
  metrics: [],
  sourceLabel: 'YouTube',
  connected: true,
};

describe('YouTubeOverviewPanel', () => {
  it('renders the channel name in the header', () => {
    render(<YouTubeOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByText('YouTube Org\u00e1nico')).toBeInTheDocument();
  });

  it('renders KPI display names', () => {
    render(<YouTubeOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getAllByText('Vistas').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Minutos Vistos')).toBeInTheDocument();
    expect(screen.getByText('% Retenci\u00f3n Promedio')).toBeInTheDocument();
  });

  it('renders the funnel section', () => {
    render(<YouTubeOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByText('Funnel de Conversi\u00f3n')).toBeInTheDocument();
  });

  it('renders the "Dashboard completo" button when onExpand is provided', () => {
    render(<YouTubeOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByLabelText('Dashboard completo')).toBeInTheDocument();
  });

  it('renders subscriber growth section', () => {
    render(<YouTubeOverviewPanel channel={CHANNEL} onClose={vi.fn()} onExpand={vi.fn()} />);
    expect(screen.getByText('Crecimiento de Suscriptores')).toBeInTheDocument();
  });
});
