'use client';

import { useMemo, useState } from 'react';
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
import type { CampaignRecommendation } from '../../../../types/metrics';

interface MetaAdsHealthCheckPanelProps {
  data: MetaHealthCheck | undefined;
  isLoading: boolean;
  onAssignClick: () => void;
  /**
   * Performance recommendations coming from the campaigns performance endpoint.
   * These are merged into the unified "Recomendaciones" section alongside
   * structural health check recommendations.
   */
  campaignRecommendations?: CampaignRecommendation[];
  /** Map of campaign externalId → display name, used to render context labels. */
  campaignNameById?: Record<string, string>;
  /** Called when the user clicks the action button on a campaign recommendation. */
  onRecommendationAction?: (rec: CampaignRecommendation) => void;
}

/** Unified shape rendered inside the Recomendaciones section. */
interface MergedRecommendation {
  key: string;
  severity: RecommendationSeverity;
  title: string;
  body: string | null;
  /** Short label describing what the recommendation is about (campaign or offer). */
  contextLabel: string | null;
  /** Optional action button (only for campaign perf recs today). */
  action?: { label: string; onClick: () => void };
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

const SEVERITY_ORDER: Record<RecommendationSeverity, number> = {
  critical: 0,
  warning: 1,
  info: 2,
};

/** Normalize Meta's importance string to our severity vocabulary. */
function importanceToSeverity(importance: string | null): RecommendationSeverity {
  const upper = (importance ?? '').toUpperCase();
  if (upper === 'CRITICAL') return 'critical';
  if (upper === 'HIGH') return 'warning';
  return 'info';
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

function MergedRecommendationCard({ rec }: { rec: MergedRecommendation }) {
  return (
    <div
      className={cn(
        'rounded-md border border-l-[3px] border-border p-3',
        severityClass(rec.severity),
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-1.5">
            <p className="text-xs font-medium text-foreground">{rec.title}</p>
            {rec.contextLabel && (
              <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">
                {rec.contextLabel}
              </span>
            )}
          </div>
          {rec.body && (
            <p className="mt-0.5 text-[11px] text-muted-foreground">{rec.body}</p>
          )}
        </div>
        {rec.action && (
          <button
            type="button"
            onClick={rec.action.onClick}
            className="shrink-0 rounded-md border border-border bg-background px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-muted"
          >
            {rec.action.label}
          </button>
        )}
      </div>
    </div>
  );
}

/** Resolve a structural recommendation's context label using the health-check data. */
function resolveStructuralContext(
  rec: Recommendation,
  data: MetaHealthCheck,
): string | null {
  if (rec.relatedOfferId) {
    const offer = data.offersCoverage.find(o => o.offerId === rec.relatedOfferId);
    if (offer) return `Offer: ${offer.offerName}`;
  }
  if (rec.relatedTargetId) {
    const campaign = data.activeCampaigns.find(
      c => c.externalId === rec.relatedTargetId,
    );
    if (campaign) return `Campaña: ${campaign.name}`;
    const unassigned = data.unassignedTargets.find(
      t => t.externalId === rec.relatedTargetId,
    );
    if (unassigned) return `Campaña: ${unassigned.name}`;
  }
  return null;
}

/** Build the "Campaña: X" (or "N campañas") context label for a campaign rec. */
function resolveCampaignContext(
  rec: CampaignRecommendation,
  campaignNameById: Record<string, string>,
): string | null {
  const ids = rec.objectIds ?? [];
  if (ids.length === 0) return null;
  if (ids.length === 1) {
    const name = campaignNameById[ids[0]];
    return name ? `Campaña: ${name}` : `Campaña: ${ids[0]}`;
  }
  return `${ids.length} campañas`;
}

export function MetaAdsHealthCheckPanel({
  data,
  isLoading,
  onAssignClick,
  campaignRecommendations,
  campaignNameById,
  onRecommendationAction,
}: MetaAdsHealthCheckPanelProps) {
  // Merge structural + campaign recommendations into a single sorted list.
  const mergedRecs = useMemo<MergedRecommendation[]>(() => {
    const items: MergedRecommendation[] = [];
    const campaignRecs = campaignRecommendations ?? [];
    const nameById = campaignNameById ?? {};

    if (data) {
      data.recommendations.forEach((rec, idx) => {
        items.push({
          key: `structural-${rec.type}-${idx}`,
          severity: rec.severity,
          title: rec.title,
          body: rec.body,
          contextLabel: resolveStructuralContext(rec, data),
        });
      });
    }

    campaignRecs.forEach((rec, idx) => {
      items.push({
        key: `campaign-${rec.recommendationType}-${idx}`,
        severity: importanceToSeverity(rec.importance),
        title: rec.title ?? 'Recomendación',
        body: rec.body,
        contextLabel: resolveCampaignContext(rec, nameById),
        action: onRecommendationAction
          ? {
              label: 'Ver en Campañas',
              onClick: () => onRecommendationAction(rec),
            }
          : undefined,
      });
    });

    return items.sort(
      (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
    );
  }, [data, campaignRecommendations, campaignNameById, onRecommendationAction]);

  const hasStructural = !!data;
  const hasContent = hasStructural || mergedRecs.length > 0;

  // Default expanded: anything non-healthy OR any recommendation to show.
  const defaultExpanded =
    (data && data.overallStatus !== 'healthy') || mergedRecs.length > 0;
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (isLoading && !hasContent) {
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

  if (!hasContent) return null;

  const overallStatus: HealthStatus = data?.overallStatus ?? 'healthy';
  const summaryText =
    data?.summaryText ??
    (mergedRecs.length > 0
      ? `${mergedRecs.length} recomendación${mergedRecs.length === 1 ? '' : 'es'} para revisar.`
      : '');
  const hasUnassigned = (data?.unassignedTargets.length ?? 0) > 0;

  return (
    <div className={cn('rounded-lg border p-4', statusBorderClass(overallStatus))}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          {statusIcon(overallStatus)}
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">Diagnóstico Meta Ads</h3>
            {summaryText && (
              <p className="mt-0.5 text-xs text-muted-foreground">{summaryText}</p>
            )}
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
          {data && data.activeCampaigns.length > 0 && (
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
          {data && data.offersCoverage.length > 0 && (
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

          {/* Merged recommendations (structural + campaign performance) */}
          {mergedRecs.length > 0 && (
            <section>
              <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                Recomendaciones
              </p>
              <div className="space-y-1.5">
                {mergedRecs.map(rec => (
                  <MergedRecommendationCard key={rec.key} rec={rec} />
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
