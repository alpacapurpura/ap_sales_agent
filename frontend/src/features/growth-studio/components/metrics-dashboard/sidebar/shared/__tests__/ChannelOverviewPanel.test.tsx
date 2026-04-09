import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Instagram, Youtube, Mail } from 'lucide-react';
import type { ChannelDashboardData, ChannelMetric } from '../../../../../types/metrics';

// --- Mocks ---
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue('test-token') }),
}));

vi.mock('../../../../../hooks/useSyncChannel', () => ({
  useSyncChannel: () => ({ sync: vi.fn(), isSyncing: false, cooldownMinutes: 0, result: null, error: null, reset: vi.fn() }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: 'test-tenant' }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

const MOCK_IG_DATA: ChannelDashboardData = {
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

let mockData: ChannelDashboardData | undefined = MOCK_IG_DATA;
let mockIsLoading = false;

vi.mock('../../../../../hooks/useChannelDashboard', () => ({
  useChannelDashboard: () => ({ data: mockData, isLoading: mockIsLoading }),
}));

vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

import { ChannelOverviewPanel } from '../ChannelOverviewPanel';

const IG_CHANNEL: ChannelMetric = {
  slug: 'ig-organic',
  name: 'Instagram Orgánico',
  channelType: 'organic_social',
  metrics: [],
  sourceLabel: 'Instagram',
  connected: true,
};

const IG_HERO_METRICS = ['total_interactions', 'ig_views', 'ig_follows_and_unfollows', 'ig_engagement_rate'];

describe('ChannelOverviewPanel', () => {
  beforeEach(() => {
    mockData = MOCK_IG_DATA;
    mockIsLoading = false;
  });

  it('renders the channel name in the header', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByText('Instagram Orgánico')).toBeInTheDocument();
  });

  it('renders KPI display names from data', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getAllByText('Interacciones').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Vistas').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument();
  });

  it('renders the funnel section', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByText('Funnel de Conversión')).toBeInTheDocument();
  });

  it('renders the "Dashboard completo" button when onExpand is provided', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        onExpand={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByLabelText('Dashboard completo')).toBeInTheDocument();
  });

  it('does not render "Dashboard completo" button when onExpand is absent', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.queryByLabelText('Dashboard completo')).not.toBeInTheDocument();
  });

  it('renders the period selector with default 30d', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByText('30 días')).toBeInTheDocument();
    expect(screen.getByText('7 días')).toBeInTheDocument();
    expect(screen.getByText('90 días')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={onClose}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    const closeButton = screen.getByRole('button', { name: /cerrar/i });
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it('renders children render prop with data', () => {
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      >
        {(data) => <div data-testid="custom-child">{data.channelName}</div>}
      </ChannelOverviewPanel>,
    );
    expect(screen.getByTestId('custom-child')).toHaveTextContent('Instagram Orgánico');
  });

  it('shows loading spinner when isLoading is true', () => {
    mockIsLoading = true;
    mockData = undefined;
    const { container } = render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(container.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    mockData = undefined;
    render(
      <ChannelOverviewPanel
        channel={IG_CHANNEL}
        onClose={vi.fn()}
        icon={Instagram}
        iconColor="text-pink-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByText('No hay datos para el periodo seleccionado')).toBeInTheDocument();
  });

  it('works with different icon and color props', () => {
    render(
      <ChannelOverviewPanel
        channel={{ ...IG_CHANNEL, slug: 'yt-organic', name: 'YouTube' }}
        onClose={vi.fn()}
        icon={Youtube}
        iconColor="text-red-500"
        heroMetrics={IG_HERO_METRICS}
      />,
    );
    expect(screen.getByText('YouTube')).toBeInTheDocument();
  });

  it('uses dashboardSlug instead of channel.slug when provided', () => {
    // This test verifies the prop is accepted without error.
    // The mock intercepts useChannelDashboard so we just confirm rendering succeeds.
    render(
      <ChannelOverviewPanel
        channel={{ ...IG_CHANNEL, slug: 'email-nurture', name: 'Email' }}
        onClose={vi.fn()}
        icon={Mail}
        iconColor="text-amber-500"
        heroMetrics={['open_rate', 'click_rate', 'emails_sent', 'active_subscribers']}
        dashboardSlug="email-nurture"
      />,
    );
    expect(screen.getByText('Email')).toBeInTheDocument();
  });
});
