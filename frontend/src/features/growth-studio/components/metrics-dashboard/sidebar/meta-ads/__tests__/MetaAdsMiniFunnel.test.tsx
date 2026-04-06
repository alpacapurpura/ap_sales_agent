import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import type { FunnelStep } from '../../../../../types/metrics';

const STEPS: FunnelStep[] = [
  { label: 'Impresiones', metricName: 'impressions', value: 10000, conversionRate: null },
  { label: 'Clics', metricName: 'clicks', value: 200, conversionRate: 2.0 },
  { label: 'Conversiones', metricName: 'conversions', value: 10, conversionRate: 5.0 },
];

describe('MetaAdsMiniFunnel', () => {
  it('renders all funnel steps', () => {
    render(<MetaAdsMiniFunnel steps={STEPS} />);
    expect(screen.getByText('Impresiones')).toBeInTheDocument();
    expect(screen.getByText('Clics')).toBeInTheDocument();
    expect(screen.getByText('Conversiones')).toBeInTheDocument();
  });

  it('shows conversion rates for non-first steps', () => {
    render(<MetaAdsMiniFunnel steps={STEPS} />);
    // conversionRate.toFixed(1) produces "2.0" and "5.0"
    expect(screen.getByText('(2.0%)')).toBeInTheDocument();
    expect(screen.getByText('(5.0%)')).toBeInTheDocument();
  });

  it('does not show conversion rate for the first step', () => {
    render(<MetaAdsMiniFunnel steps={STEPS} />);
    // First step has conversionRate=null, and i===0, so no rate shown
    const allText = screen.getByText('Impresiones').closest('div')?.textContent;
    expect(allText).not.toContain('(');
  });

  it('renders nothing for empty steps', () => {
    const { container } = render(<MetaAdsMiniFunnel steps={[]} />);
    expect(container.innerHTML).toBe('');
  });

  it('shows formatted values with locale separators', () => {
    render(<MetaAdsMiniFunnel steps={STEPS} />);
    // 10000.toLocaleString('en-US') = "10,000"
    expect(screen.getByText('10,000')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('renders the section heading', () => {
    render(<MetaAdsMiniFunnel steps={STEPS} />);
    expect(screen.getByText('Funnel de Conversión')).toBeInTheDocument();
  });

  it('renders progress bars for each step', () => {
    const { container } = render(<MetaAdsMiniFunnel steps={STEPS} />);
    // Each step renders an outer bar container and an inner bar
    const bars = container.querySelectorAll('.bg-blue-500, .bg-blue-500\\/70');
    expect(bars.length).toBeGreaterThanOrEqual(STEPS.length);
  });
});
