import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ImprovementNotesPanel } from '../ImprovementNotesPanel';
import type { ImprovementNotice } from '../types';

function makeNotice(
  overrides: Partial<ImprovementNotice> = {},
): ImprovementNotice {
  return {
    id: 'meta:CAMPAIGN_BUDGET_LEARNINGS:c1',
    category: 'campaign',
    severity: 'warning',
    title: 'Tu campaña está aprendiendo',
    body: 'Evita cambios grandes en presupuesto.',
    contextLabel: 'Campaña: Ventas PRO',
    targetExternalId: 'c1',
    ...overrides,
  };
}

describe('ImprovementNotesPanel', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders nothing when there are no notices', () => {
    const { container } = render(
      <ImprovementNotesPanel
        notices={[]}
        severity={{ critical: 0, warning: 0, info: 0 }}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders collapsed by default with the "Tienes N cosas por mejorar" header', () => {
    render(
      <ImprovementNotesPanel
        notices={[makeNotice()]}
        severity={{ critical: 0, warning: 1, info: 0 }}
      />,
    );

    expect(
      screen.getByText(/Tienes 1 cosa por mejorar/i),
    ).toBeInTheDocument();
    // Notice body should NOT be in the DOM — panel starts collapsed.
    expect(
      screen.queryByText('Evita cambios grandes en presupuesto.'),
    ).not.toBeInTheDocument();
  });

  it('uses plural form when there are multiple notices', () => {
    render(
      <ImprovementNotesPanel
        notices={[
          makeNotice({ id: '1' }),
          makeNotice({ id: '2', severity: 'critical' }),
        ]}
        severity={{ critical: 1, warning: 1, info: 0 }}
      />,
    );

    expect(
      screen.getByText(/Tienes 2 cosas por mejorar/i),
    ).toBeInTheDocument();
  });

  it('shows a severity breakdown in the header', () => {
    render(
      <ImprovementNotesPanel
        notices={[makeNotice({ severity: 'critical' }), makeNotice({ id: '2' })]}
        severity={{ critical: 1, warning: 1, info: 0 }}
      />,
    );

    // Breakdown text like "1 crítica · 1 advertencia"
    expect(screen.getByText(/1 crítica/i)).toBeInTheDocument();
    expect(screen.getByText(/1 advertencia/i)).toBeInTheDocument();
  });

  it('expands on header click and reveals the notice cards', () => {
    render(
      <ImprovementNotesPanel
        notices={[makeNotice()]}
        severity={{ critical: 0, warning: 1, info: 0 }}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /ver detalle|ocultar detalle/i }));

    expect(
      screen.getByText('Evita cambios grandes en presupuesto.'),
    ).toBeInTheDocument();
  });

  it('respects forceOpen prop (expanded on first render)', () => {
    render(
      <ImprovementNotesPanel
        notices={[makeNotice()]}
        severity={{ critical: 0, warning: 1, info: 0 }}
        forceOpen
      />,
    );

    // Body should be visible without needing to click.
    expect(
      screen.getByText('Evita cambios grandes en presupuesto.'),
    ).toBeInTheDocument();
  });

  it('calls onIgnore when the ignore button is clicked on a notice', () => {
    const onIgnore = vi.fn();
    render(
      <ImprovementNotesPanel
        notices={[makeNotice({ id: 'notice-1' })]}
        severity={{ critical: 0, warning: 1, info: 0 }}
        forceOpen
        onIgnore={onIgnore}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Ignorar/i }));

    expect(onIgnore).toHaveBeenCalledWith('notice-1');
  });

  it('calls onNoticeClick when the notice body is clicked', () => {
    const onNoticeClick = vi.fn();
    const notice = makeNotice({ id: 'notice-1' });
    render(
      <ImprovementNotesPanel
        notices={[notice]}
        severity={{ critical: 0, warning: 1, info: 0 }}
        forceOpen
        onNoticeClick={onNoticeClick}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Ver en detalle/i }));

    expect(onNoticeClick).toHaveBeenCalledWith(notice);
  });

  it('uses critical styling when any notice is critical', () => {
    const { container } = render(
      <ImprovementNotesPanel
        notices={[makeNotice({ severity: 'critical' })]}
        severity={{ critical: 1, warning: 0, info: 0 }}
      />,
    );
    // Red border class indicates critical styling.
    expect(container.querySelector('.border-red-500\\/40, .border-red-500\\/30')).toBeTruthy();
  });
});
