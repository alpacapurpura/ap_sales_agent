import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { OfferSegmenter } from '../OfferSegmenter';
import type { OfferSegmenterSelection } from '../OfferSegmenter';
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
    impressions: 0,
    clicks: 0,
    ctr: 0,
    cpm: 0,
    cpc: 0,
    reach: null,
    frequency: null,
    funnel: [],
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
    expect(
      screen.queryByRole('button', { name: /sin asignar/i }),
    ).toBeNull();

    rerender(
      <OfferSegmenter
        offers={[]}
        selectedOfferId="all"
        onSelect={vi.fn()}
        hasUnassigned={true}
        hasBranding={false}
      />,
    );
    expect(
      screen.getByRole('button', { name: /filtrar por campañas sin asignar a offer/i }),
    ).toBeInTheDocument();
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
    expect(
      screen.getByRole('button', { name: /filtrar por campañas de branding/i }),
    ).toBeInTheDocument();
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
    fireEvent.click(
      screen.getByRole('button', { name: /filtrar por campañas sin asignar a offer/i }),
    );
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

  describe('chip kind markers', () => {
    function renderAll() {
      const offers = [makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })];
      return render(
        <OfferSegmenter
          offers={offers}
          selectedOfferId="all"
          onSelect={vi.fn()}
          hasUnassigned={true}
          hasBranding={true}
        />,
      );
    }

    it('tags each chip with a data-chip-kind attribute', () => {
      renderAll();
      expect(
        screen.getByRole('button', { name: /Todas/i }),
      ).toHaveAttribute('data-chip-kind', 'all');
      expect(
        screen.getByRole('button', { name: /MasterClass/i }),
      ).toHaveAttribute('data-chip-kind', 'offer');
      expect(
        screen.getByRole('button', { name: /filtrar por campañas sin asignar/i }),
      ).toHaveAttribute('data-chip-kind', 'unassigned');
      expect(
        screen.getByRole('button', { name: /filtrar por campañas de branding/i }),
      ).toHaveAttribute('data-chip-kind', 'branding');
    });

    it('renders an AlertTriangle icon on the "Sin asignar" chip', () => {
      renderAll();
      const chip = screen.getByRole('button', {
        name: /filtrar por campañas sin asignar/i,
      });
      // lucide-react renders an <svg> with class "lucide-triangle-alert" or similar
      const svg = chip.querySelector('svg');
      expect(svg).not.toBeNull();
      expect(svg?.getAttribute('class') ?? '').toMatch(/triangle|alert/i);
    });

    it('renders a Sparkles icon on the "Branding" chip', () => {
      renderAll();
      const chip = screen.getByRole('button', {
        name: /filtrar por campañas de branding/i,
      });
      const svg = chip.querySelector('svg');
      expect(svg).not.toBeNull();
      expect(svg?.getAttribute('class') ?? '').toMatch(/sparkles/i);
    });
  });

  describe('active state check icon', () => {
    it('renders a Check icon when "Todas" is active', () => {
      render(
        <OfferSegmenter
          offers={[makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })]}
          selectedOfferId="all"
          onSelect={vi.fn()}
          hasUnassigned={false}
          hasBranding={false}
        />,
      );
      const chip = screen.getByRole('button', { name: /Todas/i });
      const check = chip.querySelector('svg.lucide-check, svg[class*="check"]');
      expect(check).not.toBeNull();
    });

    it('renders a Check icon when an offer chip is active', () => {
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
      const check = chip.querySelector('svg.lucide-check, svg[class*="check"]');
      expect(check).not.toBeNull();
    });

    it('does NOT render a Check icon when "Todas" is inactive', () => {
      render(
        <OfferSegmenter
          offers={[makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })]}
          selectedOfferId="off-1"
          onSelect={vi.fn()}
          hasUnassigned={false}
          hasBranding={false}
        />,
      );
      const chip = screen.getByRole('button', { name: /Todas/i });
      const check = chip.querySelector('svg.lucide-check, svg[class*="check"]');
      expect(check).toBeNull();
    });
  });

  describe('aria-pressed correctness across chip kinds', () => {
    it('"Sin asignar" reports pressed when selected', () => {
      render(
        <OfferSegmenter
          offers={[]}
          selectedOfferId="unassigned"
          onSelect={vi.fn()}
          hasUnassigned={true}
          hasBranding={false}
        />,
      );
      const chip = screen.getByRole('button', {
        name: /filtrar por campañas sin asignar/i,
      });
      expect(chip).toHaveAttribute('aria-pressed', 'true');
    });

    it('"Branding" reports pressed when selected', () => {
      render(
        <OfferSegmenter
          offers={[]}
          selectedOfferId="branding"
          onSelect={vi.fn()}
          hasUnassigned={false}
          hasBranding={true}
        />,
      );
      const chip = screen.getByRole('button', {
        name: /filtrar por campañas de branding/i,
      });
      expect(chip).toHaveAttribute('aria-pressed', 'true');
    });
  });

  describe('keyboard navigation (roving tabindex)', () => {
    function renderNav(selectedOfferId: 'all' | string = 'all') {
      const offers = [
        makeOffer({ offerId: 'off-1', offerName: 'MasterClass', archetype: 'PROGRAMA' }),
        makeOffer({ offerId: 'off-2', offerName: 'Servicio', archetype: 'SERVICIO' }),
      ];
      return render(
        <OfferSegmenter
          offers={offers}
          selectedOfferId={selectedOfferId}
          onSelect={vi.fn()}
          hasUnassigned={true}
          hasBranding={true}
        />,
      );
    }

    it('uses roving tabindex: only the selected chip is tabbable', () => {
      renderNav('off-1');
      expect(screen.getByRole('button', { name: /Todas/i })).toHaveAttribute(
        'tabindex',
        '-1',
      );
      expect(
        screen.getByRole('button', { name: /MasterClass/i }),
      ).toHaveAttribute('tabindex', '0');
      expect(screen.getByRole('button', { name: /Servicio/i })).toHaveAttribute(
        'tabindex',
        '-1',
      );
    });

    it('defaults tabindex=0 to the first chip when selection is not in the list', () => {
      render(
        <OfferSegmenter
          offers={[makeOffer({ offerId: 'off-1', offerName: 'MasterClass' })]}
          selectedOfferId={'ghost-id' as OfferSegmenterSelection}
          onSelect={vi.fn()}
          hasUnassigned={false}
          hasBranding={false}
        />,
      );
      expect(screen.getByRole('button', { name: /Todas/i })).toHaveAttribute(
        'tabindex',
        '0',
      );
    });

    it('ArrowRight moves focus to the next chip', () => {
      renderNav('all');
      const todas = screen.getByRole('button', { name: /Todas/i });
      todas.focus();
      expect(todas).toHaveFocus();

      fireEvent.keyDown(todas, { key: 'ArrowRight' });
      const masterClass = screen.getByRole('button', { name: /MasterClass/i });
      expect(masterClass).toHaveFocus();

      fireEvent.keyDown(masterClass, { key: 'ArrowRight' });
      expect(screen.getByRole('button', { name: /Servicio/i })).toHaveFocus();
    });

    it('ArrowDown also moves focus to the next chip', () => {
      renderNav('all');
      const todas = screen.getByRole('button', { name: /Todas/i });
      todas.focus();

      fireEvent.keyDown(todas, { key: 'ArrowDown' });
      expect(
        screen.getByRole('button', { name: /MasterClass/i }),
      ).toHaveFocus();
    });

    it('ArrowLeft moves focus to the previous chip', () => {
      renderNav('off-2');
      const servicio = screen.getByRole('button', { name: /Servicio/i });
      servicio.focus();
      expect(servicio).toHaveFocus();

      fireEvent.keyDown(servicio, { key: 'ArrowLeft' });
      expect(
        screen.getByRole('button', { name: /MasterClass/i }),
      ).toHaveFocus();
    });

    it('ArrowRight wraps around from the last chip to the first', () => {
      renderNav('all');
      const branding = screen.getByRole('button', {
        name: /filtrar por campañas de branding/i,
      });
      branding.focus();
      expect(branding).toHaveFocus();

      fireEvent.keyDown(branding, { key: 'ArrowRight' });
      expect(screen.getByRole('button', { name: /Todas/i })).toHaveFocus();
    });

    it('ArrowLeft wraps around from the first chip to the last', () => {
      renderNav('all');
      const todas = screen.getByRole('button', { name: /Todas/i });
      todas.focus();

      fireEvent.keyDown(todas, { key: 'ArrowLeft' });
      expect(
        screen.getByRole('button', {
          name: /filtrar por campañas de branding/i,
        }),
      ).toHaveFocus();
    });

    it('Home jumps focus to the first chip', () => {
      renderNav('all');
      const servicio = screen.getByRole('button', { name: /Servicio/i });
      servicio.focus();

      fireEvent.keyDown(servicio, { key: 'Home' });
      expect(screen.getByRole('button', { name: /Todas/i })).toHaveFocus();
    });

    it('End jumps focus to the last chip', () => {
      renderNav('all');
      const todas = screen.getByRole('button', { name: /Todas/i });
      todas.focus();

      fireEvent.keyDown(todas, { key: 'End' });
      expect(
        screen.getByRole('button', {
          name: /filtrar por campañas de branding/i,
        }),
      ).toHaveFocus();
    });

    it('prevents default on navigation keys (so page does not scroll)', () => {
      renderNav('all');
      const todas = screen.getByRole('button', { name: /Todas/i });
      todas.focus();
      const evt = fireEvent.keyDown(todas, { key: 'ArrowRight' });
      expect(evt).toBe(false); // returning false means defaultPrevented
    });
  });
});
