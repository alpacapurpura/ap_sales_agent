import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { OfferSegmenter } from '../OfferSegmenter';
import type { OfferMetrics } from '../../../../../types/offer-association';

function makeOffer(overrides: Partial<OfferMetrics>): OfferMetrics {
  return {
    offerId: 'off-1',
    offerName: 'MasterClass',
    archetype: 'PROGRAMA',
    expectedMetric: 'purchase',
    expectedMetricLabelEs: 'Compras',
    totalSpend: 1000,
    currency: 'PEN',
    primaryResultCount: 10,
    primaryCostPerResult: 100,
    primaryMetricName: 'Costo por compra',
    primaryMetricUnit: 'currency',
    roas: 2.1,
    secondaryMetrics: {},
    timeseries: [],
    metricUnavailableReason: null,
    ...overrides,
  };
}

describe('OfferSegmenter', () => {
  it('renders a "Todas" chip and an item for each offer', () => {
    const offers = [
      makeOffer({ offerId: 'off-1', offerName: 'MasterClass', archetype: 'PROGRAMA' }),
      makeOffer({ offerId: 'off-2', offerName: 'Servicio 1:1', archetype: 'SERVICIO' }),
    ];
    render(
      <OfferSegmenter
        offers={offers}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={false}
        hasBranding={false}
      />,
    );
    expect(screen.getByRole('button', { name: /Todas/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /MasterClass/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Servicio 1:1/i })).toBeInTheDocument();
  });

  it('renders "Sin asignar" chip only when hasUnassigned is true', () => {
    const { rerender } = render(
      <OfferSegmenter
        offers={[]}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={false}
        hasBranding={false}
      />,
    );
    expect(screen.queryByRole('button', { name: /Sin asignar/i })).toBeNull();

    rerender(
      <OfferSegmenter
        offers={[]}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={true}
        hasBranding={false}
      />,
    );
    expect(screen.getByRole('button', { name: /Sin asignar/i })).toBeInTheDocument();
  });

  it('renders "Branding" chip only when hasBranding is true', () => {
    render(
      <OfferSegmenter
        offers={[]}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={false}
        hasBranding={true}
      />,
    );
    expect(screen.getByRole('button', { name: /Branding/i })).toBeInTheDocument();
  });

  it('marks the selected chip with aria-pressed=true', () => {
    render(
      <OfferSegmenter
        offers={[makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })]}
        selectedOfferId="off-1"
        onSelect={vi.fn()}
        hasUnassigned={false}
        hasBranding={false}
      />,
    );
    const chip = screen.getByRole('button', { name: /MasterClass/i });
    expect(chip).toHaveAttribute('aria-pressed', 'true');
    const todas = screen.getByRole('button', { name: /Todas/i });
    expect(todas).toHaveAttribute('aria-pressed', 'false');
  });

  it('calls onSelect when a chip is clicked', () => {
    const onSelect = vi.fn();
    render(
      <OfferSegmenter
        offers={[makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })]}
        selectedOfferId="all"
        onSelect={onSelect}
        hasUnassigned={true}
        hasBranding={false}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /MasterClass/i }));
    expect(onSelect).toHaveBeenCalledWith('off-1');
    fireEvent.click(screen.getByRole('button', { name: /Sin asignar/i }));
    expect(onSelect).toHaveBeenCalledWith('unassigned');
  });

  it('shows the archetype emoji for each offer chip', () => {
    const offers = [makeOffer({ offerId: 'off-1', offerName: 'Curso', archetype: 'PROGRAMA' })];
    render(
      <OfferSegmenter
        offers={offers}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={false}
        hasBranding={false}
      />,
    );
    const chip = screen.getByRole('button', { name: /Curso/i });
    // PROGRAMA → 📚
    expect(chip.textContent ?? '').toContain('📚');
  });
});
