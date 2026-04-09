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
  channelSlug: 'email-nurture',
  channelName: 'Email Marketing',
  industryCategory: 'general',
  period: '30d',
  kpis: [
    { metricName: 'open_rate', displayName: 'Tasa de Apertura', currentValue: 22.5, previousValue: 20.0, deltaPct: 12.5, deltaAbsolute: 2.5, unit: 'percentage', higherIsBetter: true, benchmark: null },
    { metricName: 'click_rate', displayName: 'Tasa de Clics', currentValue: 3.1, previousValue: 2.8, deltaPct: 10.7, deltaAbsolute: 0.3, unit: 'percentage', higherIsBetter: true, benchmark: null },
    { metricName: 'emails_sent', displayName: 'Emails Enviados', currentValue: 5000, previousValue: 4500, deltaPct: 11.1, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
    { metricName: 'active_subscribers', displayName: 'Suscriptores Activos', currentValue: 12000, previousValue: 11500, deltaPct: 4.3, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
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

import { MailDashboard } from '../MailDashboard';

describe('MailDashboard', () => {
  it('renders the dashboard header with Volver button', () => {
    render(<MailDashboard isRouteBased />);
    expect(screen.getByText('Volver')).toBeInTheDocument();
  });

  it('renders all 5 tabs', () => {
    render(<MailDashboard isRouteBased />);
    expect(screen.getByRole('tab', { name: 'Resumen' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Engagement' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Entregabilidad' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Lista' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Automatización' })).toBeInTheDocument();
  });

  it('renders the period selector', () => {
    render(<MailDashboard isRouteBased />);
    expect(screen.getByText('30 días')).toBeInTheDocument();
    expect(screen.getByText('7 días')).toBeInTheDocument();
    expect(screen.getByText('90 días')).toBeInTheDocument();
  });

  it('renders the dashboard title', () => {
    const { container } = render(<MailDashboard isRouteBased />);
    expect(container.textContent).toContain('Email Marketing');
    expect(container.textContent).toContain('Dashboard');
  });
});
