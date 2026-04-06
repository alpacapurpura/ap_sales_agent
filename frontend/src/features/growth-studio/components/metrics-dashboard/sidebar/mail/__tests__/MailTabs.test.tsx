/**
 * Comprehensive unit tests for all 5 Mail Dashboard tabs.
 * Verifies that every metric, chart, tooltip, and conditional element renders
 * correctly with complete mock data.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { ChannelDashboardData, MetricKpiData, MetricTimeSeries } from '../../../../../types/metrics';

// --- Mocks ---
vi.mock('../../../../../hooks/useMetricCatalog', () => ({
  useMetricCatalog: () => ({ getTooltipData: () => null }),
}));

// --- Shared mock data factory ---

function makeTsPoints(count: number, baseValue: number) {
  return Array.from({ length: count }, (_, i) => ({
    date: `2026-04-${String(i + 1).padStart(2, '0')}`,
    value: baseValue + i * 2,
  }));
}

const BASE_KPIS: MetricKpiData[] = [
  { metricName: 'open_rate', displayName: 'Tasa de Apertura', currentValue: 22.5, previousValue: 20.0, deltaPct: 12.5, deltaAbsolute: 2.5, unit: 'percentage', higherIsBetter: true, benchmark: { low: 10, median: 18, high: 40, unit: 'percentage', interpretation: 'Promedio global 18%' } },
  { metricName: 'click_rate', displayName: 'Tasa de Clics', currentValue: 3.1, previousValue: 2.8, deltaPct: 10.7, deltaAbsolute: 0.3, unit: 'percentage', higherIsBetter: true, benchmark: { low: 1, median: 2.6, high: 4, unit: 'percentage', interpretation: 'Clics sobre enviados' } },
  { metricName: 'emails_sent', displayName: 'Emails Enviados', currentValue: 5000, previousValue: 4500, deltaPct: 11.1, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'active_subscribers', displayName: 'Suscriptores Activos', currentValue: 12000, previousValue: 11500, deltaPct: 4.3, deltaAbsolute: 500, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'click_to_open_rate', displayName: 'CTOR', currentValue: 14.1, previousValue: 13.0, deltaPct: 8.5, deltaAbsolute: 1.1, unit: 'percentage', higherIsBetter: true, benchmark: { low: 8, median: 14.1, high: 20, unit: 'percentage', interpretation: 'Calidad post-apertura' } },
  { metricName: 'bounce_rate', displayName: 'Tasa de Rebote', currentValue: 1.2, previousValue: 1.5, deltaPct: -20.0, deltaAbsolute: -0.3, unit: 'percentage', higherIsBetter: false, benchmark: null },
  { metricName: 'spam_reports', displayName: 'Spam Reports', currentValue: 3, previousValue: 2, deltaPct: 50, deltaAbsolute: 1, unit: 'count', higherIsBetter: false, benchmark: null },
  { metricName: 'unsubscribe_rate', displayName: 'Tasa Desuscripción', currentValue: 0.15, previousValue: 0.12, deltaPct: 25.0, deltaAbsolute: 0.03, unit: 'percentage', higherIsBetter: false, benchmark: null },
  { metricName: 'automation_completed', displayName: 'Automatizaciones', currentValue: 230, previousValue: 200, deltaPct: 15.0, deltaAbsolute: 30, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'completion_rate', displayName: 'Tasa Completado', currentValue: 48.5, previousValue: 45.0, deltaPct: 7.8, deltaAbsolute: 3.5, unit: 'percentage', higherIsBetter: true, benchmark: { low: 30, median: 45, high: 60, unit: 'percentage', interpretation: 'Eficacia de secuencias' } },
  { metricName: 'form_conversions', displayName: 'Conversiones Form', currentValue: 85, previousValue: 70, deltaPct: 21.4, deltaAbsolute: 15, unit: 'count', higherIsBetter: true, benchmark: null },
  { metricName: 'form_conversion_rate', displayName: 'Tasa Conversión', currentValue: 3.2, previousValue: 2.8, deltaPct: 14.3, deltaAbsolute: 0.4, unit: 'percentage', higherIsBetter: true, benchmark: null },
];

const BASE_TIME_SERIES: MetricTimeSeries[] = [
  { metricName: 'emails_sent', displayName: 'Enviados', unit: 'count', dataPoints: makeTsPoints(10, 150) },
  { metricName: 'open_rate', displayName: 'Apertura', unit: 'percentage', dataPoints: makeTsPoints(10, 18) },
  { metricName: 'unique_opens', displayName: 'Aperturas', unit: 'count', dataPoints: makeTsPoints(10, 80) },
  { metricName: 'unique_clicks', displayName: 'Clics', unit: 'count', dataPoints: makeTsPoints(10, 15) },
  { metricName: 'forwards', displayName: 'Reenvíos', unit: 'count', dataPoints: makeTsPoints(10, 3) },
  { metricName: 'click_to_open_rate', displayName: 'CTOR', unit: 'percentage', dataPoints: makeTsPoints(10, 12) },
  { metricName: 'hard_bounces', displayName: 'Rebotes Duros', unit: 'count', dataPoints: makeTsPoints(10, 2) },
  { metricName: 'soft_bounces', displayName: 'Rebotes Suaves', unit: 'count', dataPoints: makeTsPoints(10, 5) },
  { metricName: 'bounce_rate', displayName: 'Tasa Rebote', unit: 'percentage', dataPoints: makeTsPoints(10, 1) },
  { metricName: 'unsubscribe_rate', displayName: 'Desuscripción', unit: 'percentage', dataPoints: makeTsPoints(10, 0.1) },
  { metricName: 'new_subscribers', displayName: 'Nuevos', unit: 'count', dataPoints: makeTsPoints(10, 20) },
  { metricName: 'unsubscribes', displayName: 'Desuscripciones', unit: 'count', dataPoints: makeTsPoints(10, 3) },
  { metricName: 'active_subscribers', displayName: 'Activos', unit: 'count', dataPoints: makeTsPoints(10, 11800) },
  { metricName: 'completion_rate', displayName: 'Completado', unit: 'percentage', dataPoints: makeTsPoints(10, 42) },
];

const MOCK_DATA: ChannelDashboardData = {
  channelSlug: 'email-nurture',
  channelName: 'Email Marketing',
  industryCategory: 'general',
  period: '30d',
  kpis: BASE_KPIS,
  timeSeries: BASE_TIME_SERIES,
  funnel: {
    steps: [
      { label: 'Enviados', metricName: 'emails_sent', value: 5000, conversionRate: null },
      { label: 'Aperturas', metricName: 'unique_opens', value: 1000, conversionRate: 20.0 },
      { label: 'Clics', metricName: 'unique_clicks', value: 150, conversionRate: 15.0 },
      { label: 'Conversiones', metricName: 'form_conversions', value: 30, conversionRate: 20.0 },
    ],
  },
  frequencyAlert: null,
};

// ─── Lazy imports after mocks ─────────────────────────────────────────────────
import { MailOverviewTab } from '../tabs/MailOverviewTab';
import { MailEngagementTab } from '../tabs/MailEngagementTab';
import { MailEntregabilidadTab } from '../tabs/MailEntregabilidadTab';
import { MailListaTab } from '../tabs/MailListaTab';
import { MailAutomatizacionTab } from '../tabs/MailAutomatizacionTab';
import { MailDeliverabilityHealth } from '../MailDeliverabilityHealth';

// =============================================================================
// Tab 1: Overview
// =============================================================================
describe('MailOverviewTab', () => {
  it('renders hero KPI grid with 4 metrics', () => {
    const { container } = render(<MailOverviewTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('Tasa de Apertura');
    expect(container.textContent).toContain('Tasa de Clics');
    expect(container.textContent).toContain('Emails Enviados');
    expect(container.textContent).toContain('Suscriptores Activos');
  });

  it('renders the ComposedChart tooltip "Volumen vs Engagement"', () => {
    render(<MailOverviewTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Volumen vs Engagement')).toBeInTheDocument();
  });

  it('renders funnel steps', () => {
    const { container } = render(<MailOverviewTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('Enviados');
    expect(container.textContent).toContain('Aperturas');
    expect(container.textContent).toContain('Clics');
    expect(container.textContent).toContain('Conversiones');
  });

  it('renders list growth indicator', () => {
    const { container } = render(<MailOverviewTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('Crecimiento de Lista');
  });

  it('shows loading state', () => {
    const { container } = render(<MailOverviewTab data={undefined} isLoading={true} />);
    expect(container.querySelector('.animate-spin')).toBeTruthy();
  });

  it('shows empty state when no data', () => {
    render(<MailOverviewTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 2: Engagement
// =============================================================================
describe('MailEngagementTab', () => {
  it('renders 3 KPI cards: CTOR, Click Rate, Reenvíos', () => {
    const { container } = render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('CTOR')).toBeInTheDocument();
    expect(screen.getByText('Click Rate')).toBeInTheDocument();
    // "Reenvíos" appears in both KPI card and donut legend — check the KPI section exists
    const kpiSection = container.querySelector('.grid.grid-cols-3');
    expect(kpiSection?.textContent).toContain('Reenvíos');
  });

  it('renders CTOR value with one decimal', () => {
    const { container } = render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('14.1%');
  });

  it('renders Click Rate value with two decimals', () => {
    const { container } = render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('3.10%');
  });

  it('renders forwards total as sum of timeseries', () => {
    const { container } = render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    // forwards timeseries: 3,5,7,9,11,13,15,17,19,21 → sum = 120
    expect(container.textContent).toContain('120');
  });

  it('renders stacked bar chart tooltip', () => {
    render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Desglose de Engagement Diario')).toBeInTheDocument();
  });

  it('renders donut chart tooltip', () => {
    render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Distribución del Engagement')).toBeInTheDocument();
  });

  it('renders donut legend with percentage labels', () => {
    const { container } = render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('Aperturas');
    expect(container.textContent).toContain('Clics');
  });

  it('renders CTOR trend chart tooltip', () => {
    render(<MailEngagementTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Tendencia CTOR')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<MailEngagementTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 3: Entregabilidad
// =============================================================================
describe('MailEntregabilidadTab', () => {
  it('renders health score component', () => {
    const { container } = render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('Saludable');
  });

  it('renders 3 KPI cards: Bounce Rate, Spam Reports, Desuscripción', () => {
    render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Bounce Rate')).toBeInTheDocument();
    expect(screen.getByText('Spam Reports')).toBeInTheDocument();
    expect(screen.getByText('Desuscripción')).toBeInTheDocument();
  });

  it('renders bounce rate value', () => {
    const { container } = render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('1.20%');
  });

  it('renders spam count and rate', () => {
    const { container } = render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('3'); // spam count
    expect(container.textContent).toContain('0.060%'); // spam rate = 3/5000*100
  });

  it('renders unsubscribe rate value', () => {
    const { container } = render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('0.15%');
  });

  it('renders bounce breakdown chart tooltip', () => {
    render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Desglose de Rebotes')).toBeInTheDocument();
  });

  it('renders health trend chart tooltip', () => {
    render(<MailEntregabilidadTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Tendencia de Salud')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<MailEntregabilidadTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 4: Lista
// =============================================================================
describe('MailListaTab', () => {
  it('renders 2 KPI cards: Suscriptores Activos and Nuevos', () => {
    render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Suscriptores Activos')).toBeInTheDocument();
    expect(screen.getByText('Nuevos (periodo)')).toBeInTheDocument();
  });

  it('renders active subscribers value', () => {
    const { container } = render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('12,000');
  });

  it('renders new subscribers total with + prefix', () => {
    const { container } = render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    // new_subscribers: 20,22,24,...,38 → sum = 290
    expect(container.textContent).toContain('+290');
  });

  it('renders growth chart tooltip', () => {
    render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Crecimiento de Lista')).toBeInTheDocument();
  });

  it('renders churn ratio section', () => {
    render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Ratio de Churn')).toBeInTheDocument();
  });

  it('renders churn ratio with correct status text', () => {
    const { container } = render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    // unsubs: 3,5,...,21 → sum=120. newsubs sum=290. ratio=120/290*100 ≈ 41%
    expect(container.textContent).toContain('Lista creciendo');
  });

  it('renders form conversions section when data present', () => {
    render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Formularios')).toBeInTheDocument();
    expect(screen.getByText('Conversiones')).toBeInTheDocument();
    expect(screen.getByText('Tasa Conversión')).toBeInTheDocument();
  });

  it('shows delta percentage for active subscribers', () => {
    const { container } = render(<MailListaTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('+4.3% vs anterior');
  });

  it('shows empty state when no data', () => {
    render(<MailListaTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

// =============================================================================
// Tab 5: Automatización
// =============================================================================
describe('MailAutomatizacionTab', () => {
  it('renders 2 KPI cards: Automatizaciones Completadas and Tasa', () => {
    render(<MailAutomatizacionTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Automatizaciones Completadas')).toBeInTheDocument();
    expect(screen.getByText('Tasa de Completado')).toBeInTheDocument();
  });

  it('renders automation count value', () => {
    const { container } = render(<MailAutomatizacionTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('230');
  });

  it('renders completion rate value', () => {
    const { container } = render(<MailAutomatizacionTab data={MOCK_DATA} isLoading={false} />);
    expect(container.textContent).toContain('48.5%');
  });

  it('renders funnel chart tooltip', () => {
    render(<MailAutomatizacionTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Funnel de Automatización')).toBeInTheDocument();
  });

  it('renders completion rate trend tooltip', () => {
    render(<MailAutomatizacionTab data={MOCK_DATA} isLoading={false} />);
    expect(screen.getByText('Tendencia Tasa de Completado')).toBeInTheDocument();
  });

  it('shows empty state when no data', () => {
    render(<MailAutomatizacionTab data={undefined} isLoading={false} />);
    expect(screen.getByText('No hay datos disponibles')).toBeInTheDocument();
  });
});

// =============================================================================
// MailDeliverabilityHealth (shared component)
// =============================================================================
describe('MailDeliverabilityHealth', () => {
  it('shows healthy status with good metrics', () => {
    const { container } = render(<MailDeliverabilityHealth kpis={BASE_KPIS} />);
    expect(container.textContent).toContain('Saludable');
  });

  it('shows warning status with elevated bounce rate', () => {
    const warningKpis = BASE_KPIS.map(k =>
      k.metricName === 'bounce_rate' ? { ...k, currentValue: 3.5 } : k,
    );
    const { container } = render(<MailDeliverabilityHealth kpis={warningKpis} />);
    expect(container.textContent).toContain('Atención');
  });

  it('shows critical status with high bounce + high unsub', () => {
    const criticalKpis = BASE_KPIS.map(k => {
      if (k.metricName === 'bounce_rate') return { ...k, currentValue: 8.0 };
      if (k.metricName === 'unsubscribe_rate') return { ...k, currentValue: 0.8 };
      return k;
    });
    const { container } = render(<MailDeliverabilityHealth kpis={criticalKpis} />);
    expect(container.textContent).toContain('Crítico');
  });

  it('displays score out of 100', () => {
    const { container } = render(<MailDeliverabilityHealth kpis={BASE_KPIS} />);
    expect(container.textContent).toMatch(/\/100/);
  });
});
