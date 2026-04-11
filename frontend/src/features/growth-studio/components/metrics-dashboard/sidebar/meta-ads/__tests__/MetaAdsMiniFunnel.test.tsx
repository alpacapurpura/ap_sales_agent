/**
 * Tests for MetaAdsMiniFunnel.
 *
 * Focus areas (per UI-SPEC §6):
 *  - Steps render with correct label, formatted value, and proportional bar
 *  - Conversion rate is visible between steps (not only on hover) and uses
 *    the color ramp
 *  - Color ramp thresholds (emerald/lime/amber/orange/red) are applied
 *    consistently to both the rate row and the receiving step's bar
 *  - Empty state varies by filter (all/offer/branding/unassigned)
 *  - Partial-zero steps render with a 0% rate and 0-width bar — NOT "—"
 *  - Accessibility: role="list", narrative aria-label per step
 *
 * Tooltip hover content is partially covered: Radix hides the TooltipContent
 * in the DOM until focus/hover. We verify the trigger wiring (help icon +
 * rate row) and leave live-open rendering to E2E.
 */

import React from 'react';
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { TooltipProvider } from '@/components/ui/tooltip';

import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import type { FunnelStep } from '../../../../../types/metrics';

function renderFunnel(ui: React.ReactElement) {
  // All tooltips in the real app live inside a TooltipProvider on ResumenTab.
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

const STEPS: FunnelStep[] = [
  { label: 'Impresiones', metricName: 'impressions', value: 12340, conversionRate: null },
  { label: 'Clics', metricName: 'clicks', value: 518, conversionRate: 4.2 },
  { label: 'Vistas de Landing', metricName: 'meta_landing_page_views', value: 352, conversionRate: 68.0 },
  { label: 'Leads', metricName: 'meta_leads', value: 47, conversionRate: 13.4 },
  { label: 'Conversiones', metricName: 'conversions', value: 6, conversionRate: 12.7 },
];

describe('MetaAdsMiniFunnel — rendering', () => {
  it('renders every step with its label and en-US formatted value', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={STEPS} />);
    expect(screen.getByText('Impresiones')).toBeInTheDocument();
    expect(screen.getByText('Clics')).toBeInTheDocument();
    expect(screen.getByText('Vistas de Landing')).toBeInTheDocument();
    expect(screen.getByText('Leads')).toBeInTheDocument();
    expect(screen.getByText('Conversiones')).toBeInTheDocument();

    expect(screen.getAllByText('12,340').length).toBeGreaterThan(0);
    expect(screen.getAllByText('518').length).toBeGreaterThan(0);
    expect(screen.getAllByText('352').length).toBeGreaterThan(0);
    expect(screen.getAllByText('47').length).toBeGreaterThan(0);
    expect(screen.getAllByText('6').length).toBeGreaterThan(0);
  });

  it('uses role="list" and role="listitem" with narrative aria-labels', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={STEPS} />);
    const list = screen.getByRole('list', { name: /embudo de conversión/i });
    expect(list).toBeInTheDocument();

    const items = within(list).getAllByRole('listitem');
    expect(items).toHaveLength(STEPS.length);

    // First step: no rate suffix.
    expect(items[0]).toHaveAttribute('aria-label', 'Impresiones: 12,340');
    // Subsequent: includes narrative rate and previous step reference.
    expect(items[1]?.getAttribute('aria-label')).toMatch(
      /Clics: 518, tasa del 4\.2% desde Impresiones/,
    );
    expect(items[4]?.getAttribute('aria-label')).toMatch(
      /Conversiones: 6, tasa del 12\.7% desde Leads/,
    );
  });

  it('does not render a rate row before the first step', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={STEPS} />);
    // Only N-1 rate rows for N steps. The arrow+text shows the rate value;
    // check by counting downwards arrow occurrences via aria on the row.
    // Each rate row renders exactly one ArrowDown lucide svg with the rate.
    const rateTexts = screen.getAllByText(/^\d+(\.\d+)?%$/);
    expect(rateTexts).toHaveLength(STEPS.length - 1);
  });

  it('renders zero steps with a muted bar and 0% rate (NOT "—")', () => {
    const steps: FunnelStep[] = [
      { label: 'Impresiones', metricName: 'impressions', value: 10_000, conversionRate: null },
      { label: 'Clics', metricName: 'clicks', value: 200, conversionRate: 2.0 },
      { label: 'Leads', metricName: 'meta_leads', value: 0, conversionRate: 0 },
    ];
    renderFunnel(<MetaAdsMiniFunnel steps={steps} />);

    // Leads row is present with value "0" (not an em-dash).
    expect(screen.getByText('Leads')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThan(0);
    expect(screen.queryByText('—')).not.toBeInTheDocument();

    // Rate row for 0% is visible.
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('renders nothing when steps array is empty', () => {
    const { container } = renderFunnel(<MetaAdsMiniFunnel steps={[]} />);
    expect(container.querySelector('[role="list"]')).toBeNull();
  });
});

describe('MetaAdsMiniFunnel — color ramp', () => {
  function setupWithRate(rate: number) {
    const steps: FunnelStep[] = [
      { label: 'A', metricName: 'impressions', value: 1_000, conversionRate: null },
      { label: 'B', metricName: 'clicks', value: 10, conversionRate: rate },
    ];
    return renderFunnel(<MetaAdsMiniFunnel steps={steps} />);
  }

  it('colors ≥25% rates in emerald', () => {
    const { container } = setupWithRate(30);
    expect(container.querySelector('.text-emerald-500')).not.toBeNull();
    expect(container.querySelector('.bg-emerald-500')).not.toBeNull();
  });

  it('colors 10–25% rates in lime', () => {
    const { container } = setupWithRate(15);
    expect(container.querySelector('.text-lime-500')).not.toBeNull();
    expect(container.querySelector('.bg-lime-500')).not.toBeNull();
  });

  it('colors 3–10% rates in amber', () => {
    const { container } = setupWithRate(5);
    expect(container.querySelector('.text-amber-500')).not.toBeNull();
    expect(container.querySelector('.bg-amber-500')).not.toBeNull();
  });

  it('colors 0.5–3% rates in orange', () => {
    const { container } = setupWithRate(1.2);
    expect(container.querySelector('.text-orange-500')).not.toBeNull();
    expect(container.querySelector('.bg-orange-500')).not.toBeNull();
  });

  it('colors <0.5% rates in red', () => {
    const { container } = setupWithRate(0.2);
    expect(container.querySelector('.text-red-500')).not.toBeNull();
    expect(container.querySelector('.bg-red-500')).not.toBeNull();
  });

  it('uses neutral blue for the first step bar (no rate to compare)', () => {
    const { container } = setupWithRate(30);
    expect(container.querySelector('.bg-blue-500')).not.toBeNull();
  });
});

describe('MetaAdsMiniFunnel — empty state', () => {
  const ZERO_STEPS: FunnelStep[] = [
    { label: 'Impresiones', metricName: 'impressions', value: 0, conversionRate: null },
    { label: 'Clics', metricName: 'clicks', value: 0, conversionRate: null },
    { label: 'Leads', metricName: 'meta_leads', value: 0, conversionRate: null },
  ];

  it('renders the all-filter empty state by default', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={ZERO_STEPS} />);
    expect(
      screen.getByText(/sin actividad medible en este período/i),
    ).toBeInTheDocument();
  });

  it('renders the offer-specific empty state when filter="offer"', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={ZERO_STEPS} filter="offer" />);
    expect(
      screen.getByText(/esta offer aún no tiene campañas asignadas/i),
    ).toBeInTheDocument();
  });

  it('renders the branding-specific empty state when filter="branding"', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={ZERO_STEPS} filter="branding" />);
    expect(
      screen.getByText(/sin impresiones de branding en este período/i),
    ).toBeInTheDocument();
  });

  it('renders the unassigned-specific empty state when filter="unassigned"', () => {
    renderFunnel(<MetaAdsMiniFunnel steps={ZERO_STEPS} filter="unassigned" />);
    expect(
      screen.getByText(/las campañas sin asignar no reportaron eventos/i),
    ).toBeInTheDocument();
  });

  it('does NOT render empty state if any step has data', () => {
    const steps: FunnelStep[] = [
      { label: 'Impresiones', metricName: 'impressions', value: 100, conversionRate: null },
      ...ZERO_STEPS.slice(1),
    ];
    renderFunnel(<MetaAdsMiniFunnel steps={steps} />);
    expect(
      screen.queryByText(/sin actividad medible en este período/i),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('list')).toBeInTheDocument();
  });
});

describe('MetaAdsMiniFunnel — bar width', () => {
  it('first step bar width is 100%', () => {
    const { container } = renderFunnel(<MetaAdsMiniFunnel steps={STEPS} />);
    // Find all .h-full bars (inner fill). First should be width: 100%.
    const bars = container.querySelectorAll<HTMLDivElement>('.h-full.rounded-full');
    expect(bars.length).toBe(STEPS.length);
    expect(bars[0]?.style.width).toBe('100%');
  });

  it('applies the 2% floor for small-but-nonzero values', () => {
    const steps: FunnelStep[] = [
      { label: 'A', metricName: 'impressions', value: 1_000_000, conversionRate: null },
      { label: 'B', metricName: 'clicks', value: 1, conversionRate: 0.0001 },
    ];
    const { container } = renderFunnel(<MetaAdsMiniFunnel steps={steps} />);
    const bars = container.querySelectorAll<HTMLDivElement>('.h-full.rounded-full');
    // 1 / 1_000_000 * 100 = 0.0001% → floored to 2%.
    expect(bars[1]?.style.width).toBe('2%');
  });

  it('keeps width at 0% when the value is exactly 0', () => {
    const steps: FunnelStep[] = [
      { label: 'A', metricName: 'impressions', value: 1_000, conversionRate: null },
      { label: 'B', metricName: 'clicks', value: 0, conversionRate: 0 },
    ];
    const { container } = renderFunnel(<MetaAdsMiniFunnel steps={steps} />);
    const bars = container.querySelectorAll<HTMLDivElement>('.h-full.rounded-full');
    expect(bars[1]?.style.width).toBe('0%');
  });
});
