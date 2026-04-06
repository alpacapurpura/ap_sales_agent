import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { MetricKpiData, MetricTimeSeries } from '../../../../../types/metrics';

vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

import { MailHeroKpiGrid } from '../MailHeroKpiGrid';

const MOCK_KPIS: MetricKpiData[] = [
  { metricName: 'open_rate', displayName: 'Tasa de Apertura', currentValue: 22.5, previousValue: 20.0, deltaPct: 12.5, deltaAbsolute: 2.5, unit: 'percentage', higherIsBetter: true, benchmark: null },
  { metricName: 'click_rate', displayName: 'Tasa de Clics', currentValue: 3.1, previousValue: 2.8, deltaPct: 10.7, deltaAbsolute: 0.3, unit: 'percentage', higherIsBetter: true, benchmark: null },
  { metricName: 'emails_sent', displayName: 'Emails Enviados', currentValue: 5000, previousValue: 4500, deltaPct: 11.1, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'active_subscribers', displayName: 'Suscriptores Activos', currentValue: 12000, previousValue: 11500, deltaPct: 4.3, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
];

const MOCK_TIME_SERIES: MetricTimeSeries[] = [];

describe('MailHeroKpiGrid', () => {
  it('renders 4 KPI cards', () => {
    const { container } = render(
      <MailHeroKpiGrid kpis={MOCK_KPIS} timeSeries={MOCK_TIME_SERIES} />,
    );
    const cards = container.querySelectorAll('.rounded-lg.border.bg-card');
    expect(cards.length).toBe(4);
  });

  it('renders metric display names', () => {
    render(<MailHeroKpiGrid kpis={MOCK_KPIS} timeSeries={MOCK_TIME_SERIES} />);
    expect(screen.getByText('Tasa de Apertura')).toBeInTheDocument();
    expect(screen.getByText('Tasa de Clics')).toBeInTheDocument();
    expect(screen.getByText('Emails Enviados')).toBeInTheDocument();
    expect(screen.getByText('Suscriptores Activos')).toBeInTheDocument();
  });

  it('renders formatted values', () => {
    const { container } = render(
      <MailHeroKpiGrid kpis={MOCK_KPIS} timeSeries={MOCK_TIME_SERIES} />,
    );
    expect(container.textContent).toContain('22.50%');
    expect(container.textContent).toContain('3.10%');
    expect(container.textContent).toContain('5.0k');
    expect(container.textContent).toContain('12k');
  });

  it('renders delta percentages', () => {
    const { container } = render(
      <MailHeroKpiGrid kpis={MOCK_KPIS} timeSeries={MOCK_TIME_SERIES} />,
    );
    expect(container.textContent).toContain('12.5%');
    expect(container.textContent).toContain('10.7%');
  });
});
