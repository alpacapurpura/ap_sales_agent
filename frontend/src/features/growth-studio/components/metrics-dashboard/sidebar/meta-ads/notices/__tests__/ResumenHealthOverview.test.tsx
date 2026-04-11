import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ResumenHealthOverview } from '../ResumenHealthOverview';
import type { NoticesSummary } from '../types';

function makeSummary(overrides: Partial<NoticesSummary> = {}): NoticesSummary {
  const base: NoticesSummary = {
    byTab: { campanas: [], creativos: [], audiencia: [], costos: [] },
    total: 0,
    perTabCounts: { campanas: 0, creativos: 0, audiencia: 0, costos: 0 },
    severity: { critical: 0, warning: 0, info: 0 },
    severityPerTab: {
      campanas: { critical: 0, warning: 0, info: 0 },
      creativos: { critical: 0, warning: 0, info: 0 },
      audiencia: { critical: 0, warning: 0, info: 0 },
      costos: { critical: 0, warning: 0, info: 0 },
    },
    maxSeverityPerTab: {
      campanas: null,
      creativos: null,
      audiencia: null,
      costos: null,
    },
  };
  return { ...base, ...overrides };
}

describe('ResumenHealthOverview', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('shows the celebratory empty state when there are zero notices', () => {
    render(
      <ResumenHealthOverview summary={makeSummary()} onNavigateToTab={vi.fn()} />,
    );

    expect(screen.getByText(/Todo en orden/i)).toBeInTheDocument();
    expect(
      screen.queryByText(/cosas por mejorar/i),
    ).not.toBeInTheDocument();
  });

  it('shows "Tienes N cosas por mejorar" header when there are notices', () => {
    render(
      <ResumenHealthOverview
        summary={makeSummary({
          total: 3,
          perTabCounts: { campanas: 2, creativos: 1, audiencia: 0, costos: 0 },
          severity: { critical: 1, warning: 2, info: 0 },
          maxSeverityPerTab: {
            campanas: 'critical',
            creativos: 'warning',
            audiencia: null,
            costos: null,
          },
        })}
        onNavigateToTab={vi.fn()}
      />,
    );

    expect(screen.getByText(/Tienes 3 cosas por mejorar/i)).toBeInTheDocument();
  });

  it('starts collapsed and expands on click', () => {
    render(
      <ResumenHealthOverview
        summary={makeSummary({
          total: 1,
          perTabCounts: { campanas: 1, creativos: 0, audiencia: 0, costos: 0 },
          severity: { critical: 0, warning: 1, info: 0 },
          maxSeverityPerTab: {
            campanas: 'warning',
            creativos: null,
            audiencia: null,
            costos: null,
          },
        })}
        onNavigateToTab={vi.fn()}
      />,
    );

    // Initially collapsed: per-tab rows not visible.
    expect(screen.queryByRole('button', { name: /Ir a Campañas/i })).toBeNull();

    fireEvent.click(
      screen.getByRole('button', { name: /ver detalle/i }),
    );

    expect(
      screen.getByRole('button', { name: /Ir a Campañas/i }),
    ).toBeInTheDocument();
  });

  it('calls onNavigateToTab when a tab CTA is clicked', () => {
    const onNav = vi.fn();
    render(
      <ResumenHealthOverview
        summary={makeSummary({
          total: 2,
          perTabCounts: { campanas: 0, creativos: 2, audiencia: 0, costos: 0 },
          severity: { critical: 0, warning: 2, info: 0 },
          maxSeverityPerTab: {
            campanas: null,
            creativos: 'warning',
            audiencia: null,
            costos: null,
          },
        })}
        onNavigateToTab={onNav}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /ver detalle/i }),
    );
    fireEvent.click(
      screen.getByRole('button', { name: /Ir a Creativos/i }),
    );

    expect(onNav).toHaveBeenCalledWith('creativos');
  });

  it('only lists tabs that actually have pending notices', () => {
    render(
      <ResumenHealthOverview
        summary={makeSummary({
          total: 1,
          perTabCounts: { campanas: 1, creativos: 0, audiencia: 0, costos: 0 },
          severity: { critical: 0, warning: 1, info: 0 },
          maxSeverityPerTab: {
            campanas: 'warning',
            creativos: null,
            audiencia: null,
            costos: null,
          },
        })}
        onNavigateToTab={vi.fn()}
      />,
    );

    fireEvent.click(
      screen.getByRole('button', { name: /ver detalle/i }),
    );

    expect(
      screen.getByRole('button', { name: /Ir a Campañas/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: /Ir a Creativos/i }),
    ).toBeNull();
    expect(
      screen.queryByRole('button', { name: /Ir a Audiencia/i }),
    ).toBeNull();
    expect(
      screen.queryByRole('button', { name: /Ir a Costos/i }),
    ).toBeNull();
  });
});
