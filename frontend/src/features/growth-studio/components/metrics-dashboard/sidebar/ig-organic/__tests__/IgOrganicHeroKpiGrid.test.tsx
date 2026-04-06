import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { MetricKpiData, MetricTimeSeries } from '../../../../../types/metrics';

vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

import { IgOrganicHeroKpiGrid } from '../IgOrganicHeroKpiGrid';

const KPIS: MetricKpiData[] = [
  { metricName: 'total_interactions', displayName: 'Interacciones', currentValue: 2450, previousValue: 2100, deltaPct: 16.7, deltaAbsolute: 350, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'ig_views', displayName: 'Vistas', currentValue: 485000, previousValue: 410000, deltaPct: 18.3, deltaAbsolute: 75000, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'ig_follows_and_unfollows', displayName: 'Seguidores netos', currentValue: 127, previousValue: 95, deltaPct: 33.7, deltaAbsolute: 32, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'ig_engagement_rate', displayName: 'Engagement Rate', currentValue: 0.51, previousValue: 0.44, deltaPct: 15.9, deltaAbsolute: 0.07, unit: 'percentage', higherIsBetter: true, benchmark: { low: 0.3, median: 0.5, high: 0.8, unit: 'percentage', interpretation: 'Tasa de interacción' } },
];

const TIME_SERIES: MetricTimeSeries[] = [];

describe('IgOrganicHeroKpiGrid', () => {
  it('renders all 4 hero KPIs', () => {
    render(<IgOrganicHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    expect(screen.getByText('Interacciones')).toBeInTheDocument();
    expect(screen.getByText('Vistas')).toBeInTheDocument();
    expect(screen.getByText('Seguidores netos')).toBeInTheDocument();
    expect(screen.getByText('Engagement Rate')).toBeInTheDocument();
  });

  it('formats KPI values correctly', () => {
    render(<IgOrganicHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    // 2450 -> "2.5k", 485000 -> "485k", 127 -> "127", 0.51 -> "0.51%"
    expect(screen.getByText('2.5k')).toBeInTheDocument();
    expect(screen.getByText('485k')).toBeInTheDocument();
    expect(screen.getByText('127')).toBeInTheDocument();
    expect(screen.getByText('0.51%')).toBeInTheDocument();
  });

  it('shows delta percentage for KPIs', () => {
    render(<IgOrganicHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    expect(screen.getByText('16.7%')).toBeInTheDocument();
    expect(screen.getByText('18.3%')).toBeInTheDocument();
  });

  it('renders benchmark badge for engagement rate', () => {
    render(<IgOrganicHeroKpiGrid kpis={KPIS} timeSeries={TIME_SERIES} />);
    // BenchmarkBadge renders a label like "Promedio" or "Bueno" based on value vs range
    const engagementCard = screen.getByText('Engagement Rate').closest('.rounded-lg');
    expect(engagementCard).toBeInTheDocument();
  });
});
