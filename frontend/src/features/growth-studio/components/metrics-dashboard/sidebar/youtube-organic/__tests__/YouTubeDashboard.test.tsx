import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChannelDashboardData } from '../../../../../types/metrics';

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
    { metricName: 'avg_view_percentage', displayName: '% Retenci\u00f3n Promedio', currentValue: 52.3, previousValue: 48.1, deltaPct: 8.7, deltaAbsolute: 4.2, unit: 'percentage', higherIsBetter: true, benchmark: { low: 30, median: 50, high: 70, unit: 'percentage', interpretation: 'Retenci\u00f3n' } },
  ],
  timeSeries: [],
  funnel: {
    steps: [
      { label: 'Vistas', metricName: 'views', value: 125000, conversionRate: null },
      { label: 'Engagement', metricName: 'engagement', value: 4500, conversionRate: 3.6 },
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

vi.mock('../../../../../hooks/useYoutubeAnalytics', () => ({
  useYoutubeTopVideos: () => ({ data: [], isLoading: false }),
  useYoutubeTrafficSources: () => ({ data: [], isLoading: false }),
  useYoutubeDemographics: () => ({ data: [], isLoading: false }),
  useYoutubeCountries: () => ({ data: [], isLoading: false }),
}));

import { YouTubeDashboard } from '../YouTubeDashboard';

describe('YouTubeDashboard', () => {
  it('renders the dashboard header with Volver button', () => {
    render(<YouTubeDashboard isRouteBased />);
    expect(screen.getByText('Volver')).toBeInTheDocument();
  });

  it('renders all 5 tabs', () => {
    render(<YouTubeDashboard isRouteBased />);
    expect(screen.getByRole('tab', { name: 'Resumen' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Videos' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Audiencia' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Engagement' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /Retenci\u00f3n/ })).toBeInTheDocument();
  });

  it('renders the period selector', () => {
    render(<YouTubeDashboard isRouteBased />);
    expect(screen.getByText('30 d\u00edas')).toBeInTheDocument();
    expect(screen.getByText('7 d\u00edas')).toBeInTheDocument();
    expect(screen.getByText('90 d\u00edas')).toBeInTheDocument();
  });

  it('renders the dashboard title', () => {
    const { container } = render(<YouTubeDashboard isRouteBased />);
    expect(container.textContent).toContain('YouTube Org\u00e1nico');
    expect(container.textContent).toContain('Dashboard');
  });

  it('defaults to overview tab', () => {
    render(<YouTubeDashboard isRouteBased />);
    expect(screen.getByRole('tab', { name: 'Resumen' })).toHaveAttribute('data-state', 'active');
  });
});
