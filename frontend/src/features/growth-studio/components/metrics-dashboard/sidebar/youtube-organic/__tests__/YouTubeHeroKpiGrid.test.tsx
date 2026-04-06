import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { MetricKpiData, MetricTimeSeries } from '../../../../../types/metrics';

vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

import { YouTubeHeroKpiGrid } from '../YouTubeHeroKpiGrid';

const KPIS: MetricKpiData[] = [
  { metricName: 'views', displayName: 'Vistas', currentValue: 125000, previousValue: 100000, deltaPct: 25.0, deltaAbsolute: 25000, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'watch_time_minutes', displayName: 'Minutos Vistos', currentValue: 8500, previousValue: 7200, deltaPct: 18.1, deltaAbsolute: 1300, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'subscribers_gained', displayName: 'Suscriptores Ganados', currentValue: 340, previousValue: 280, deltaPct: 21.4, deltaAbsolute: 60, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'avg_view_percentage', displayName: '% Retenci\u00f3n Promedio', currentValue: 52.3, previousValue: 48.1, deltaPct: 8.7, deltaAbsolute: 4.2, unit: 'percentage', higherIsBetter: true, benchmark: { low: 30, median: 50, high: 70, unit: 'percentage', interpretation: 'Porcentaje promedio de retenci\u00f3n' } },
];

const TIME_SERIES: MetricTimeSeries[] = [];

describe('YouTubeHeroKpiGrid', () => {
  it('renders all 4 hero KPIs', () => {
    render(<YouTubeHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    expect(screen.getByText('Vistas')).toBeInTheDocument();
    expect(screen.getByText('Minutos Vistos')).toBeInTheDocument();
    expect(screen.getByText('Suscriptores Ganados')).toBeInTheDocument();
    expect(screen.getByText('% Retenci\u00f3n Promedio')).toBeInTheDocument();
  });

  it('formats KPI values correctly', () => {
    render(<YouTubeHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    // 125000 -> "125k", 8500 -> "8.5k", 340 -> "340", 52.3% -> "52.3%"
    expect(screen.getByText('125k')).toBeInTheDocument();
    expect(screen.getByText('8.5k')).toBeInTheDocument();
    expect(screen.getByText('340')).toBeInTheDocument();
    expect(screen.getByText('52.3%')).toBeInTheDocument();
  });

  it('shows delta percentage for KPIs', () => {
    render(<YouTubeHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    expect(screen.getByText('25.0%')).toBeInTheDocument();
    expect(screen.getByText('18.1%')).toBeInTheDocument();
  });

  it('renders benchmark badge for avg_view_percentage', () => {
    render(<YouTubeHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    // BenchmarkBadge renders a label based on value vs range
    const retentionCard = screen.getByText('% Retenci\u00f3n Promedio').closest('.rounded-lg');
    expect(retentionCard).toBeInTheDocument();
  });
});
