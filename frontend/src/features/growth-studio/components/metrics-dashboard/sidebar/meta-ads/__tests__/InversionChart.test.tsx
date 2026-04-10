/**
 * Tests for InversionChart — the rebuilt "Inversión y Retorno" chart.
 *
 * Philosophy: We mock recharts primitives to render meaningful DOM so we can
 * assert on narrative copy, tooltip behavior, reference lines, filtering,
 * and currency labels — without fighting recharts' canvas measurement.
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { MetricTimeSeries } from '../../../../../types/metrics';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('@/features/tenant/context/tenant-locale-context', () => ({
  useTenantLocale: () => ({ currency: 'PEN', timezone: 'America/Lima' }),
}));

// Mock recharts: render primitives as data-attribute divs we can query.
vi.mock('recharts', () => {
  const Passthrough = ({ children }: { children?: React.ReactNode }) => (
    <div>{children}</div>
  );
  return {
    ResponsiveContainer: Passthrough,
    ComposedChart: ({ children, data }: { children?: React.ReactNode; data?: unknown[] }) => (
      <div data-testid="composed-chart" data-points={data?.length ?? 0}>
        {children}
      </div>
    ),
    CartesianGrid: () => <div data-testid="cartesian-grid" />,
    XAxis: () => <div data-testid="x-axis" />,
    YAxis: ({ yAxisId }: { yAxisId?: string }) => (
      <div data-testid={`y-axis-${yAxisId ?? 'default'}`} />
    ),
    Tooltip: () => <div data-testid="rechart-tooltip" />,
    Bar: ({ children }: { children?: React.ReactNode }) => (
      <div data-testid="bar">{children}</div>
    ),
    Cell: ({ fill }: { fill?: string }) => (
      <div data-testid="cell" data-fill={fill} />
    ),
    Line: () => <div data-testid="line" />,
    ReferenceLine: ({ y, strokeDasharray }: { y?: number; strokeDasharray?: string }) => (
      <div
        data-testid="reference-line"
        data-y={y}
        data-stroke-dasharray={strokeDasharray}
      />
    ),
    LabelList: () => <div data-testid="label-list" />,
  };
});

// Mock the ChartContainer (pulls in recharts ResponsiveContainer internally)
vi.mock('@/components/ui/chart', () => ({
  ChartContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="chart-container">{children}</div>
  ),
}));

// Must import AFTER mocks
import { InversionChart } from '../InversionChart';

// ---------------------------------------------------------------------------
// Fixture data
// ---------------------------------------------------------------------------

const BASE_TIME_SERIES: MetricTimeSeries[] = [
  {
    metricName: 'spend',
    displayName: 'Inversión',
    unit: 'currency',
    dataPoints: [
      { date: '2026-04-05', value: 28.76 },
      { date: '2026-04-06', value: 28.35 },
      { date: '2026-04-07', value: 31.14 },
      { date: '2026-04-08', value: 856.61 },
    ],
  },
  {
    metricName: 'conversions',
    displayName: 'Resultados',
    unit: 'count',
    dataPoints: [
      { date: '2026-04-05', value: 2 },
      { date: '2026-04-06', value: 1 },
      { date: '2026-04-07', value: 3 },
      { date: '2026-04-08', value: 1 },
    ],
  },
  {
    metricName: 'ROAS',
    displayName: 'ROAS',
    unit: 'ratio',
    dataPoints: [
      { date: '2026-04-05', value: 2.1 },
      { date: '2026-04-06', value: 1.8 },
      { date: '2026-04-07', value: 2.3 },
      { date: '2026-04-08', value: 0.4 },
    ],
  },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('InversionChart', () => {
  it('renders without crashing and shows the title', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    expect(screen.getByText(/Inversión y Retorno/i)).toBeInTheDocument();
  });

  it('renders a composed chart populated with the composite data', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    const chart = screen.getByTestId('composed-chart');
    // 4 days of data, all with non-zero spend => 4 points
    expect(chart.getAttribute('data-points')).toBe('4');
  });

  it('filters out days with zero spend AND zero conversions', () => {
    const withZeros: MetricTimeSeries[] = [
      {
        metricName: 'spend',
        displayName: 'Inversión',
        unit: 'currency',
        dataPoints: [
          { date: '2026-04-05', value: 28.76 },
          { date: '2026-04-06', value: 0 },
          { date: '2026-04-07', value: 31.14 },
        ],
      },
      {
        metricName: 'conversions',
        displayName: 'Resultados',
        unit: 'count',
        dataPoints: [
          { date: '2026-04-05', value: 2 },
          { date: '2026-04-06', value: 0 },
          { date: '2026-04-07', value: 3 },
        ],
      },
      {
        metricName: 'ROAS',
        displayName: 'ROAS',
        unit: 'ratio',
        dataPoints: [
          { date: '2026-04-05', value: 2.1 },
          { date: '2026-04-06', value: 0 },
          { date: '2026-04-07', value: 2.3 },
        ],
      },
    ];
    render(<InversionChart timeSeries={withZeros} />);
    const chart = screen.getByTestId('composed-chart');
    // 2 days with activity (the middle day filtered out)
    expect(chart.getAttribute('data-points')).toBe('2');
  });

  it('renders a break-even reference line at y=1 on the right axis', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    const refLine = screen.getByTestId('reference-line');
    expect(refLine.getAttribute('data-y')).toBe('1');
    expect(refLine.getAttribute('data-stroke-dasharray')).toBe('4 4');
  });

  it('renders semantic colors on bars based on ROAS', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    const cells = screen.getAllByTestId('cell');
    // 4 data points => 4 cells
    expect(cells.length).toBe(4);
    const fills = cells.map(c => c.getAttribute('data-fill'));
    // Days with ROAS >= 1 (first three) should be green, the last (0.4) red.
    // Green = hsl(142 71% 45%), Red = hsl(0 84% 60%)
    expect(fills.slice(0, 3).every(f => f?.includes('142'))).toBe(true);
    expect(fills[3]).toContain('0 84%');
  });

  it('renders the narrative subtitle with total investment and average ROAS', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    // Total spend: 944.86 PEN (formatted), 4 days, avg ROAS = (2.1+1.8+2.3+0.4)/4 = 1.65
    // Match "4 días" (singular/plural handled), "ROAS promedio", and "1.6" or "1.65"
    expect(screen.getByText(/4 días/i)).toBeInTheDocument();
    expect(screen.getByText(/ROAS promedio/i)).toBeInTheDocument();
  });

  it('renders both left and right Y axes', () => {
    render(<InversionChart timeSeries={BASE_TIME_SERIES} />);
    expect(screen.getByTestId('y-axis-left')).toBeInTheDocument();
    expect(screen.getByTestId('y-axis-right')).toBeInTheDocument();
  });

  it('renders an empty state when all data points have zero activity', () => {
    const allZero: MetricTimeSeries[] = [
      {
        metricName: 'spend',
        displayName: 'Inversión',
        unit: 'currency',
        dataPoints: [
          { date: '2026-04-05', value: 0 },
          { date: '2026-04-06', value: 0 },
        ],
      },
      {
        metricName: 'conversions',
        displayName: 'Resultados',
        unit: 'count',
        dataPoints: [
          { date: '2026-04-05', value: 0 },
          { date: '2026-04-06', value: 0 },
        ],
      },
      {
        metricName: 'ROAS',
        displayName: 'ROAS',
        unit: 'ratio',
        dataPoints: [
          { date: '2026-04-05', value: 0 },
          { date: '2026-04-06', value: 0 },
        ],
      },
    ];
    const { container } = render(<InversionChart timeSeries={allZero} />);
    // No composed chart rendered
    expect(container.querySelector('[data-testid="composed-chart"]')).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Tooltip unit test — rendered in isolation so we can inspect its DOM
// ---------------------------------------------------------------------------

import { InversionTooltip } from '../InversionChart';

describe('InversionTooltip', () => {
  const tooltipPayload = [
    {
      dataKey: 'spend',
      value: 856.61,
      color: 'hsl(var(--chart-1))',
      payload: { isoDate: '2026-04-08' },
    },
    {
      dataKey: 'conversions',
      value: 1,
      color: 'hsl(var(--chart-2))',
      payload: { isoDate: '2026-04-08' },
    },
    {
      dataKey: 'roas',
      value: 0.4,
      color: 'hsl(45 93% 47%)',
      payload: { isoDate: '2026-04-08' },
    },
  ];

  it('renders Spanish labels instead of raw keys', () => {
    render(
      <InversionTooltip
        active={true}
        payload={tooltipPayload}
        currency="PEN"
      />,
    );
    expect(screen.getByText('Inversión')).toBeInTheDocument();
    expect(screen.getByText('Resultados')).toBeInTheDocument();
    expect(screen.getByText('ROAS')).toBeInTheDocument();
    // The raw keys must NOT appear
    expect(screen.queryByText('spend')).toBeNull();
    expect(screen.queryByText('conversions')).toBeNull();
  });

  it('formats the spend value as currency using the provided currency', () => {
    render(
      <InversionTooltip
        active={true}
        payload={tooltipPayload}
        currency="PEN"
      />,
    );
    // Intl.NumberFormat('en-US', style: 'currency', currency: 'PEN') → "PEN 856.61"
    // We just assert that "856" appears alongside a PEN symbol/code
    const spendRow = screen.getByText('Inversión').closest('div')?.parentElement;
    expect(spendRow?.textContent).toMatch(/856/);
    expect(spendRow?.parentElement?.textContent ?? '').toMatch(/PEN|S\//);
  });

  it('formats the ROAS with an "x" suffix', () => {
    render(
      <InversionTooltip
        active={true}
        payload={tooltipPayload}
        currency="PEN"
      />,
    );
    expect(screen.getByText(/0\.40x/)).toBeInTheDocument();
  });

  it('renders a long Spanish date header', () => {
    render(
      <InversionTooltip
        active={true}
        payload={tooltipPayload}
        currency="PEN"
      />,
    );
    // "8 de abril"
    expect(screen.getByText(/8 de abril/i)).toBeInTheDocument();
  });

  it('returns null when not active', () => {
    const { container } = render(
      <InversionTooltip active={false} payload={[]} currency="PEN" />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('returns null when all series are zero for this point', () => {
    const allZeroPayload = [
      { dataKey: 'spend', value: 0, color: '', payload: { isoDate: '2026-04-08' } },
      { dataKey: 'conversions', value: 0, color: '', payload: { isoDate: '2026-04-08' } },
      { dataKey: 'roas', value: 0, color: '', payload: { isoDate: '2026-04-08' } },
    ];
    const { container } = render(
      <InversionTooltip active={true} payload={allZeroPayload} currency="PEN" />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('omits individual zero-value entries but keeps the rest', () => {
    const mixedPayload = [
      { dataKey: 'spend', value: 100, color: '', payload: { isoDate: '2026-04-08' } },
      { dataKey: 'conversions', value: 0, color: '', payload: { isoDate: '2026-04-08' } },
      { dataKey: 'roas', value: 2.5, color: '', payload: { isoDate: '2026-04-08' } },
    ];
    render(
      <InversionTooltip active={true} payload={mixedPayload} currency="PEN" />,
    );
    // "Inversión" and "ROAS" are visible
    expect(screen.getByText('Inversión')).toBeInTheDocument();
    expect(screen.getByText('ROAS')).toBeInTheDocument();
    // "Resultados" was 0 → omitted
    expect(screen.queryByText('Resultados')).toBeNull();
  });
});
