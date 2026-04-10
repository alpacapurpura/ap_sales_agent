import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { MetaAdsHealthCheckPanel } from '../MetaAdsHealthCheckPanel';
import type { MetaHealthCheck } from '../../../../../types/offer-association';

const HEALTHY: MetaHealthCheck = {
  overallStatus: 'healthy',
  activeCampaigns: [
    {
      externalId: 'camp-1',
      name: 'Venta MasterClass',
      objective: 'OUTCOME_SALES',
      objectiveLabelEs: 'Ventas',
      status: 'ACTIVE',
      offerAssociation: null,
      expectedOutcomeEs: 'Compras directas via checkout',
      hasIssue: false,
      issueText: null,
    },
  ],
  offersCoverage: [
    {
      offerId: 'off-1',
      offerName: 'MasterClass',
      archetype: 'PROGRAMA',
      expectedMetric: 'purchase',
      expectedMetricLabelEs: 'Compras',
      hasActiveCampaign: true,
      associatedTargets: [],
    },
  ],
  unassignedTargets: [],
  recommendations: [],
  summaryText: 'Todo en orden: 1 campaña activa cubriendo 1 offer.',
};

const NEEDS_ATTENTION: MetaHealthCheck = {
  overallStatus: 'needs_attention',
  activeCampaigns: [
    {
      externalId: 'camp-2',
      name: 'Tráfico general',
      objective: 'OUTCOME_TRAFFIC',
      objectiveLabelEs: 'Tráfico',
      status: 'ACTIVE',
      offerAssociation: null,
      expectedOutcomeEs: 'Esta campaña busca clicks, no compras — para ver ROAS necesitás una campaña con objetivo de Ventas',
      hasIssue: true,
      issueText: 'Objective desalineado con offer',
    },
  ],
  offersCoverage: [
    {
      offerId: 'off-1',
      offerName: 'Servicio 1:1',
      archetype: 'SERVICIO',
      expectedMetric: 'message',
      expectedMetricLabelEs: 'Mensajes',
      hasActiveCampaign: false,
      associatedTargets: [],
    },
  ],
  unassignedTargets: [
    {
      targetType: 'campaign',
      externalId: 'camp-3',
      name: 'Alcance',
      objective: 'OUTCOME_AWARENESS',
      status: 'ACTIVE',
    },
  ],
  recommendations: [
    {
      type: 'create_campaign',
      severity: 'warning',
      title: 'Crea una campaña para Servicio 1:1',
      body: 'Este offer no tiene campañas activas.',
      actionLabel: 'Crear campaña',
      actionUrl: null,
      relatedOfferId: 'off-1',
      relatedTargetId: null,
    },
  ],
  summaryText: 'Tenés 1 campaña con problemas y 1 offer sin cobertura.',
};

describe('MetaAdsHealthCheckPanel', () => {
  it('renders loading skeleton when isLoading=true', () => {
    const { container } = render(
      <MetaAdsHealthCheckPanel data={undefined} isLoading={true} onAssignClick={vi.fn()} />,
    );
    expect(container.querySelector('[data-testid="health-panel-loading"]')).not.toBeNull();
  });

  it('renders null when no data and not loading', () => {
    const { container } = render(
      <MetaAdsHealthCheckPanel data={undefined} isLoading={false} onAssignClick={vi.fn()} />,
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders healthy summary text and green status when healthy', () => {
    render(<MetaAdsHealthCheckPanel data={HEALTHY} isLoading={false} onAssignClick={vi.fn()} />);
    expect(screen.getByText(/Todo en orden/i)).toBeInTheDocument();
    // "Diagnóstico" heading should exist
    expect(screen.getByText(/Diagn/i)).toBeInTheDocument();
  });

  it('lists active campaigns with their objective', () => {
    render(
      <MetaAdsHealthCheckPanel data={HEALTHY} isLoading={false} onAssignClick={vi.fn()} />,
    );
    // Need to expand first since default collapsed when healthy
    const toggle = screen.getByRole('button', { name: /ver detalle|ocultar/i });
    fireEvent.click(toggle);
    expect(screen.getByText(/Venta MasterClass/)).toBeInTheDocument();
    expect(screen.getByText(/Ventas/)).toBeInTheDocument();
  });

  it('expanded by default when needs_attention', () => {
    render(
      <MetaAdsHealthCheckPanel
        data={NEEDS_ATTENTION}
        isLoading={false}
        onAssignClick={vi.fn()}
      />,
    );
    // Campaigns section is visible without clicking
    expect(screen.getByText(/Tráfico general/)).toBeInTheDocument();
    // Servicio 1:1 appears both in offers coverage AND in the recommendation title
    expect(screen.getAllByText(/Servicio 1:1/).length).toBeGreaterThan(0);
  });

  it('shows recommendations list when present', () => {
    render(
      <MetaAdsHealthCheckPanel
        data={NEEDS_ATTENTION}
        isLoading={false}
        onAssignClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Crea una campaña para Servicio 1:1/)).toBeInTheDocument();
  });

  it('shows "Asociar campañas" button when there are unassigned targets', () => {
    const onAssign = vi.fn();
    render(
      <MetaAdsHealthCheckPanel
        data={NEEDS_ATTENTION}
        isLoading={false}
        onAssignClick={onAssign}
      />,
    );
    const btn = screen.getByRole('button', { name: /Asociar campañas/i });
    fireEvent.click(btn);
    expect(onAssign).toHaveBeenCalled();
  });

  it('does NOT show "Asociar campañas" button when no unassigned targets', () => {
    render(<MetaAdsHealthCheckPanel data={HEALTHY} isLoading={false} onAssignClick={vi.fn()} />);
    expect(screen.queryByRole('button', { name: /Asociar campañas/i })).toBeNull();
  });

  it('marks offers without campaigns as "Sin campaña"', () => {
    render(
      <MetaAdsHealthCheckPanel
        data={NEEDS_ATTENTION}
        isLoading={false}
        onAssignClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/Sin campaña/i)).toBeInTheDocument();
  });
});
