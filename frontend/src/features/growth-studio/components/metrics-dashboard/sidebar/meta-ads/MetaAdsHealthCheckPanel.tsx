'use client';

import { useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { archetypeEmoji } from '../../../../types/offer-association';
import type {
  MetaHealthCheck,
  HealthStatus,
  CampaignHealth,
  OfferCoverage,
  Recommendation,
  RecommendationSeverity,
} from '../../../../types/offer-association';

interface MetaAdsHealthCheckPanelProps {
  data: MetaHealthCheck | undefined;
  isLoading: boolean;
  onAssignClick: () => void;
}

function statusIcon(status: HealthStatus) {
  if (status === 'healthy') {
    return <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />;
  }
  if (status === 'needs_attention') {
    return <AlertTriangle className="h-5 w-5 text-amber-500" aria-hidden="true" />;
  }
  return <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />;
}

function statusBorderClass(status: HealthStatus): string {
  switch (status) {
    case 'healthy':
      return 'border-emerald-500/30 bg-emerald-500/5';
    case 'needs_attention':
      return 'border-amber-500/30 bg-amber-500/5';
    case 'critical':
      return 'border-red-500/30 bg-red-500/5';
  }
}

function severityClass(severity: RecommendationSeverity): string {
  switch (severity) {
    case 'info':
      return 'border-l-blue-500 bg-blue-500/5';
    case 'warning':
      return 'border-l-amber-500 bg-amber-500/5';
    case 'critical':
      return 'border-l-red-500 bg-red-500/5';
  }
}

function CampaignHealthRow({ campaign }: { campaign: CampaignHealth }) {
  return (
    <div
      className={cn(
        'flex items-start justify-between gap-3 rounded-md border px-3 py-2',
        campaign.hasIssue ? 'border-amber-500/30 bg-amber-500/5' : 'border-border bg-card',
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium truncate">{campaign.name}</p>
          <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
            {campaign.objectiveLabelEs}
          </span>
          {campaign.offerAssociation?.offerName && (
            <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-0.5 text-[10px] font-medium text-blue-400">
              {campaign.offerAssociation.offerName}
            </span>
          )}
        </div>
        <p className="mt-1 text-[11px] text-muted-foreground">
          {campaign.expectedOutcomeEs}
        </p>
        {campaign.hasIssue && campaign.issueText && (
          <p className="mt-1 text-[11px] text-amber-400">
            <AlertTriangle className="inline h-3 w-3 mr-1 align-[-1px]" aria-hidden="true" />
            {campaign.issueText}
          </p>
        )}
      </div>
    </div>
  );
}

function OfferCoverageRow({ offer }: { offer: OfferCoverage }) {
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border border-border bg-card px-3 py-1.5">
      <div className="flex items-center gap-2 min-w-0">
        <span aria-hidden="true">{archetypeEmoji(offer.archetype)}</span>
        <p className="text-xs font-medium truncate">{offer.offerName}</p>
        <span className="text-[10px] text-muted-foreground">
          {offer.expectedMetricLabelEs}
        </span>
      </div>
      <span
        className={cn(
          'inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium',
          offer.hasActiveCampaign
            ? 'bg-emerald-500/10 text-emerald-400'
            : 'bg-zinc-500/10 text-zinc-400',
        )}
      >
        {offer.hasActiveCampaign ? 'Con campaña' : 'Sin campaña'}
      </span>
    </div>
  );
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  return (
    <div
      className={cn(
        'rounded-md border border-l-[3px] border-border p-3',
        severityClass(rec.severity),
      )}
    >
      <p className="text-xs font-medium text-foreground">{rec.title}</p>
      {rec.body && <p className="mt-0.5 text-[11px] text-muted-foreground">{rec.body}</p>}
    </div>
  );
}

export function MetaAdsHealthCheckPanel({
  data,
  isLoading,
  onAssignClick,
}: MetaAdsHealthCheckPanelProps) {
  const defaultExpanded = data?.overallStatus !== 'healthy';
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (isLoading) {
    return (
      <div
        data-testid="health-panel-loading"
        className="rounded-lg border bg-card p-4 animate-pulse"
      >
        <div className="h-4 w-48 rounded bg-muted" />
        <div className="mt-2 h-3 w-64 rounded bg-muted" />
      </div>
    );
  }

  if (!data) return null;

  const hasUnassigned = data.unassignedTargets.length > 0;

  return (
    <div className={cn('rounded-lg border p-4', statusBorderClass(data.overallStatus))}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {statusIcon(data.overallStatus)}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">Diagnóstico Meta Ads</h3>
            <p className="mt-0.5 text-xs text-muted-foreground">{data.summaryText}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded(v => !v)}
          aria-label={expanded ? 'Ocultar detalle' : 'Ver detalle'}
          className="shrink-0 rounded-md p-1 text-muted-foreground hover:text-foreground"
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Active campaigns */}
          {data.activeCampaigns.length > 0 && (
            <section>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Campañas activas
              </p>
              <div className="space-y-1.5">
                {data.activeCampaigns.map(campaign => (
                  <CampaignHealthRow key={campaign.externalId} campaign={campaign} />
                ))}
              </div>
            </section>
          )}

          {/* Offers coverage */}
          {data.offersCoverage.length > 0 && (
            <section>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Cobertura por offer
              </p>
              <div className="space-y-1">
                {data.offersCoverage.map(offer => (
                  <OfferCoverageRow key={offer.offerId} offer={offer} />
                ))}
              </div>
            </section>
          )}

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <section>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Recomendaciones
              </p>
              <div className="space-y-1.5">
                {data.recommendations.map((rec, idx) => (
                  <RecommendationCard key={`${rec.type}-${idx}`} rec={rec} />
                ))}
              </div>
            </section>
          )}

          {/* Assign CTA */}
          {hasUnassigned && (
            <div className="flex justify-end">
              <Button
                type="button"
                size="sm"
                onClick={onAssignClick}
                className="gap-1.5"
              >
                Asociar campañas →
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
