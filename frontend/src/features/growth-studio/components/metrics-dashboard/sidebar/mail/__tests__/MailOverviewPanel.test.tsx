import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChannelDashboardData, ChannelMetric } from '../../../../../types/metrics';

vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue('test-token') }),
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
  funnel: { steps: [
    { label: 'Enviados', metricName: 'emails_sent', value: 5000, conversionRate: null },
    { label: 'Aperturas', metricName: 'unique_opens', value: 1000, conversionRate: 20.0 },
    { label: 'Clics', metricName: 'unique_clicks', value: 150, conversionRate: 15.0 },
    { label: 'Conversiones', metricName: 'form_conversions', value: 30, conversionRate: 20.0 },
  ] },
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

import { MailOverviewPanel } from '../MailOverviewPanel';

const MOCK_CHANNEL: ChannelMetric = {
  slug: 'email-nurture',
  name: 'eMailing Nurturing',
  channelType: 'automation',
  connected: true,
  metrics: [],
  sourceLabel: 'MailerLite',
  value: 0,
};

describe('MailOverviewPanel', () => {
  it('renders the panel header with Mail icon', () => {
    render(<MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} />);
    expect(screen.getByText('eMailing Nurturing')).toBeInTheDocument();
  });

  it('renders the period selector', () => {
    render(<MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} />);
    expect(screen.getByText('30 días')).toBeInTheDocument();
  });

  it('renders the expand button when onExpand is provided', () => {
    const onExpand = vi.fn();
    render(<MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} onExpand={onExpand} />);
    expect(screen.getByText('Dashboard completo')).toBeInTheDocument();
  });

  it('renders hero KPIs', () => {
    const { container } = render(
      <MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} />,
    );
    expect(container.textContent).toContain('Tasa de Apertura');
    expect(container.textContent).toContain('22.50%');
  });

  it('renders funnel steps', () => {
    const { container } = render(
      <MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} />,
    );
    expect(container.textContent).toContain('Enviados');
    expect(container.textContent).toContain('Aperturas');
  });

  it('renders deliverability health', () => {
    const { container } = render(
      <MailOverviewPanel channel={MOCK_CHANNEL} onClose={vi.fn()} />,
    );
    expect(container.textContent).toContain('Saludable');
  });
});
