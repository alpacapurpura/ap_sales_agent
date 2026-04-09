import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChannelDashboardData } from '../../../../../types/metrics';

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

const MOCK_DATA: ChannelDashboardData = {
  channelSlug: 'ig-organic',
  channelName: 'Instagram Orgánico',
  industryCategory: 'education',
  period: '30d',
  kpis: [
    { metricName: 'total_interactions', displayName: 'Interacciones', currentValue: 2450, previousValue: 2100, deltaPct: 16.7, deltaAbsolute: 350, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_views', displayName: 'Vistas', currentValue: 485000, previousValue: 410000, deltaPct: 18.3, deltaAbsolute: 75000, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_follows_and_unfollows', displayName: 'Seguidores netos', currentValue: 127, previousValue: 95, deltaPct: 33.7, deltaAbsolute: 32, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'ig_engagement_rate', displayName: 'Engagement Rate', currentValue: 0.51, previousValue: 0.44, deltaPct: 15.9, deltaAbsolute: 0.07, unit: 'percentage', higherIsBetter: true, benchmark: null },
  ],
  timeSeries: [],
  funnel: { steps: [] },
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

import { IgOrganicDashboard } from '../IgOrganicDashboard';

describe('IgOrganicDashboard', () => {
  it('renders the dashboard header with Volver button', () => {
    render(<IgOrganicDashboard isRouteBased />);
    expect(screen.getByText('Volver')).toBeInTheDocument();
  });

  it('renders all 4 tabs', () => {
    render(<IgOrganicDashboard isRouteBased />);
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Contenido' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Audiencia' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Alcance' })).toBeInTheDocument();
  });

  it('renders the period selector', () => {
    render(<IgOrganicDashboard isRouteBased />);
    expect(screen.getByText('30 días')).toBeInTheDocument();
    expect(screen.getByText('7 días')).toBeInTheDocument();
    expect(screen.getByText('90 días')).toBeInTheDocument();
  });

  it('renders the dashboard title', () => {
    const { container } = render(<IgOrganicDashboard isRouteBased />);
    expect(container.textContent).toContain('Instagram Orgánico');
    expect(container.textContent).toContain('Dashboard');
  });
});
