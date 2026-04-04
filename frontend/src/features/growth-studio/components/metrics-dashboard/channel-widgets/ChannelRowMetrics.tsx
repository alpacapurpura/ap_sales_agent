'use client';

import React from 'react';
import type { MetricValue, MetricClickData, StageId } from '../../../types/metrics';
import { METRIC_LABELS } from '../../../lib/metric-labels';
import { CostLink } from './CostLink';

/* ── Formatting helpers ──────────────────────────────────────────────── */

/** Breakdown key -> Spanish label. */
const BREAKDOWN_LABELS: Record<string, string> = {
  likes: 'likes',
  comments: 'comentarios',
  shares: 'compartidos',
  saves: 'guardados',
  reactions: 'reacciones',
  campaigns: 'Campanas',
  seo: 'SEO',
  ai_search: 'AI Search',
  google_ads: 'Google Ads',
  direct: 'Directo',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return n.toLocaleString();
}

function formatCurrency(n: number, currency?: string): string {
  const symbol = currency === 'USD' || !currency ? '$' : currency;
  return `${symbol}${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatBreakdown(breakdown: Record<string, number>): string {
  return Object.entries(breakdown)
    .filter(([, v]) => v > 0)
    .map(([key, val]) => `${BREAKDOWN_LABELS[key] ?? key} ${formatNumber(val)}`)
    .join(', ');
}

/* ── MetricDisplay (internal) ────────────────────────────────────────── */

interface MetricDisplayProps {
  metric: MetricValue;
  channelSlug?: string;
  stageId?: StageId;
  onMetricClick?: (metric: MetricClickData) => void;
  catalogByName?: Record<string, { display_name: string; interpretation: string; formula?: string }>;
}

function MetricDisplay({ metric, channelSlug, stageId, onMetricClick, catalogByName }: MetricDisplayProps) {
  const catalogEntry = catalogByName?.[metric.name];
  const label = catalogEntry?.display_name ?? METRIC_LABELS[metric.name] ?? metric.name;
  const isCurrency = metric.unit === 'currency';
  const formatted = isCurrency
    ? formatCurrency(metric.value, metric.currency)
    : formatNumber(metric.value);

  const canClick = onMetricClick && channelSlug && stageId;

  const tooltipText = catalogEntry?.interpretation
    ? `${label}${catalogEntry.formula ? ` (${catalogEntry.formula})` : ''}: ${catalogEntry.interpretation}`
    : `Ver detalle: ${label}`;

  const content = (
    <div className="flex flex-col items-end min-w-[52px]">
      <span className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">{label}</span>
      <span className="text-sm font-semibold tabular-nums leading-tight">{formatted}</span>
      {metric.breakdown && Object.keys(metric.breakdown).length > 0 && (
        <span className="text-[10px] text-muted-foreground truncate max-w-[180px]">
          {formatBreakdown(metric.breakdown)}
        </span>
      )}
    </div>
  );

  if (canClick) {
    return (
      <button
        onClick={() => onMetricClick({
          stageId,
          channelSlug,
          metricName: metric.name,
          currentValue: metric.value,
          currency: metric.currency,
        })}
        className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded-md transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
        title={tooltipText}
      >
        {content}
      </button>
    );
  }

  return <div title={tooltipText}>{content}</div>;
}

/* ── ChannelRowMetrics ───────────────────────────────────────────────── */

export interface ChannelRowMetricsProps {
  /** Filtered display metrics (excluding conversations, already summary-filtered) */
  displayMetrics: MetricValue[];
  /** Channel slug for metric click context */
  channelSlug: string;
  /** Whether the channel is connected (used for CostLink rendering) */
  connected: boolean;
  /** Stage context for metric click data */
  stageId?: StageId;
  /** Conversations metric for secondary line on leads */
  conversationsMetric?: MetricValue;
  /** Whether the channel has no data */
  hasNoData: boolean;
  /** Whether the channel has a zero leads metric */
  hasZeroLeads: boolean;
  /** Catalog entries for display_name resolution */
  catalogByName: Record<string, { display_name: string; interpretation: string; formula?: string }>;
  /** Callback when user clicks a metric value */
  onMetricClick?: (metric: MetricClickData) => void;
}

export const ChannelRowMetrics = React.memo(function ChannelRowMetrics({
  displayMetrics,
  channelSlug,
  connected,
  stageId,
  conversationsMetric,
  hasNoData,
  hasZeroLeads,
  catalogByName,
  onMetricClick,
}: ChannelRowMetricsProps) {
  if (hasNoData && !hasZeroLeads) {
    return (
      <div className="flex flex-col items-end">
        <span className="text-sm font-semibold text-muted-foreground">---</span>
        <span className="text-[10px] text-muted-foreground">Sin datos</span>
      </div>
    );
  }

  if (hasZeroLeads) {
    return (
      <div className="flex flex-col items-end">
        <span className="text-sm font-semibold text-muted-foreground">0 leads</span>
        <span className="text-[10px] text-muted-foreground">Sin actividad en los ultimos 30 dias</span>
      </div>
    );
  }

  return (
    <>
      {displayMetrics.map((m) => {
        // CostLink for unconfigured costs (value is 0/null and channel is connected)
        if (m.name === 'cost' && m.unit === 'currency' && m.value === 0 && connected) {
          return <CostLink key={m.name} />;
        }

        // Leads metric with conversations secondary line
        if (m.name === 'leads' && conversationsMetric) {
          const canClick = onMetricClick && stageId;
          const leadsLabel = catalogByName[m.name]?.display_name ?? METRIC_LABELS[m.name] ?? m.name;
          const leadsContent = (
            <div className="flex flex-col items-end min-w-[52px]">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide leading-tight">
                {leadsLabel}
              </span>
              <span className="text-sm font-semibold tabular-nums leading-tight">{formatNumber(m.value)}</span>
              <span className="text-[10px] text-muted-foreground">
                de {conversationsMetric.value.toLocaleString('es-ES')} conversaciones
              </span>
            </div>
          );
          if (canClick) {
            return (
              <button
                key={m.name}
                onClick={() => onMetricClick({
                  stageId,
                  channelSlug,
                  metricName: m.name,
                  currentValue: m.value,
                })}
                className="cursor-pointer hover:bg-primary/5 px-1.5 py-1 rounded-md transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-primary/20"
                title={`Ver detalle: ${leadsLabel}`}
              >
                {leadsContent}
              </button>
            );
          }
          return <div key={m.name}>{leadsContent}</div>;
        }

        return (
          <MetricDisplay
            key={m.name}
            metric={m}
            channelSlug={channelSlug}
            stageId={stageId}
            onMetricClick={onMetricClick}
            catalogByName={catalogByName}
          />
        );
      })}
    </>
  );
});
