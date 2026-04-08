'use client';

import { Eye, Film, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { formatMoney } from '@/lib/format-money';
import { ChartSection } from '../../shared/ChartSection';
import {
  useCreativesOverview,
  useAdPerformance,
  useFormatComparison,
} from '../../../../../api/campaigns-api';
import type { AdMetrics, FormatComparisonItem } from '../../../../../api/campaigns-api';
import type { ChannelDashboardData, MetaAdsPeriod } from '../../../../../types/metrics';

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

// ── Helpers ──────────────────────────────────────────────────────────

function formatCompact(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}k`;
  return value.toFixed(0);
}

function roasColor(roas: number | null): string {
  if (roas == null) return 'text-muted-foreground';
  if (roas >= 3) return 'text-emerald-400';
  if (roas >= 1) return 'text-amber-400';
  return 'text-red-400';
}

function cpaColor(cpa: number | null, roas: number | null): string {
  if (cpa == null) return 'text-muted-foreground';
  if (roas != null && roas >= 3) return 'text-emerald-400';
  if (roas != null && roas < 1) return 'text-red-400';
  return '';
}

function performanceTagLabel(tag: string): { label: string; className: string } {
  switch (tag) {
    case 'top_performer':
      return { label: 'Top performer', className: 'bg-emerald-500/10 text-emerald-400' };
    case 'underperformer':
      return { label: 'Peor rendimiento', className: 'bg-red-500/10 text-red-400' };
    default:
      return { label: '', className: '' };
  }
}

function formatTypeBadge(formatType: string): { label: string; className: string } {
  switch (formatType) {
    case 'video':
      return { label: 'Video', className: 'bg-blue-500/10 text-blue-400' };
    case 'carousel':
      return { label: 'Carrusel', className: 'bg-blue-500/10 text-blue-400' };
    case 'image':
      return { label: 'Imagen', className: 'bg-zinc-500/10 text-zinc-400' };
    default:
      return { label: formatType, className: 'bg-zinc-500/10 text-zinc-400' };
  }
}

// ── Ad Card ──────────────────────────────────────────────────────────

function AdCard({ ad }: { ad: AdMetrics }) {
  const isUnderperformer = ad.performanceTag === 'underperformer';
  const tagInfo = performanceTagLabel(ad.performanceTag);
  const formatInfo = formatTypeBadge(ad.formatType);

  return (
    <div
      className={cn(
        'rounded-xl border bg-card p-3 space-y-3',
        isUnderperformer && 'border-red-500/20',
      )}
    >
      {/* Thumbnail */}
      {ad.thumbnailUrl ? (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={ad.thumbnailUrl}
          alt={ad.adName}
          className="h-32 w-full rounded-lg object-cover"
        />
      ) : (
        <div className="h-32 rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground">
          Sin preview
        </div>
      )}

      {/* Name + Campaign */}
      <div>
        <p className="text-xs font-medium truncate">{ad.adName}</p>
        <p className="text-[10px] text-muted-foreground truncate">
          {ad.campaignName ?? 'Sin campa\u00f1a'}
        </p>
      </div>

      {/* KPIs Grid */}
      <div className="grid grid-cols-3 gap-2 text-center">
        <div>
          <p className="text-[9px] text-muted-foreground">ROAS</p>
          <p className={cn('text-sm font-bold', roasColor(ad.roas))}>
            {ad.roas != null ? `${ad.roas.toFixed(1)}x` : '-'}
          </p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">Ventas</p>
          <p className="text-sm font-bold">{formatCompact(ad.conversions)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground">CPA</p>
          <p className={cn('text-sm font-bold', cpaColor(ad.cpa, ad.roas))}>
            {ad.cpa != null ? formatMoney(ad.cpa, 'USD') : '-'}
          </p>
        </div>
      </div>

      {/* Badges */}
      <div className="flex items-center gap-1">
        {tagInfo.label && (
          <span className={cn('rounded-full px-2 py-0.5 text-[9px]', tagInfo.className)}>
            {tagInfo.label}
          </span>
        )}
        <span className={cn('rounded-full px-2 py-0.5 text-[9px]', formatInfo.className)}>
          {formatInfo.label}
        </span>
      </div>
    </div>
  );
}

// ── Format Comparison Row ────────────────────────────────────────────

function FormatRow({ format }: { format: FormatComparisonItem }) {
  const scoreColor =
    format.performanceScore >= 70
      ? 'bg-emerald-500/60'
      : format.performanceScore >= 40
        ? 'bg-amber-500/60'
        : 'bg-red-500/60';

  const valueColor =
    format.performanceScore >= 70
      ? 'text-emerald-400'
      : format.performanceScore >= 40
        ? 'text-amber-400'
        : 'text-red-400';

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">{format.emoji}</span>
          <span className="text-xs">{format.formatType}</span>
        </div>
        <div className="flex items-center gap-4 text-xs tabular-nums">
          <span>
            CTR <strong className={valueColor}>{(format.avgCtr * 100).toFixed(1)}%</strong>
          </span>
          <span>
            CPA{' '}
            <strong className={valueColor}>
              {format.avgCpa != null ? formatMoney(format.avgCpa, 'USD') : '-'}
            </strong>
          </span>
          <span>
            ROAS{' '}
            <strong className={valueColor}>
              {format.avgRoas != null ? `${format.avgRoas.toFixed(1)}x` : '-'}
            </strong>
          </span>
        </div>
      </div>
      <div className="w-full rounded-full bg-muted h-2">
        <div
          className={cn('h-2 rounded-full', scoreColor)}
          style={{ width: `${Math.min(format.performanceScore, 100)}%` }}
        />
      </div>
    </div>
  );
}

// ── Main Component ──────────────────────────────────────────────────

export function CreativosTab({ data, isLoading, period }: CreativosTabProps) {
  const activePeriod = period ?? '30d';
  const { data: creatives } = useCreativesOverview(activePeriod);
  const { data: adPerf, isLoading: isAdPerfLoading } = useAdPerformance(activePeriod, 3);
  const { data: formatComp } = useFormatComparison(activePeriod);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const topAds = adPerf?.ads ?? [];
  const formats = formatComp?.formats ?? [];
  const retention = creatives?.videoRetention;
  const hasRetention = retention && retention.plays > 0;

  return (
    <div className="space-y-6">
      {/* ── Top Anuncios por Rendimiento ─────────────────────────── */}
      <ChartSection slug="top-creativos">
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Top anuncios por rendimiento
          </h3>

          {isAdPerfLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : topAds.length > 0 ? (
            <div className="grid grid-cols-3 gap-3">
              {topAds.map(ad => (
                <AdCard key={ad.adId} ad={ad} />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
              <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
              <p className="font-medium">Sin datos de rendimiento por anuncio</p>
              <p className="mt-1 text-xs">
                Los datos aparecerán cuando haya anuncios activos con métricas de rendimiento.
              </p>
            </div>
          )}
        </div>
      </ChartSection>

      {/* ── 2-Column: Format Comparison + Video Retention ────────── */}
      <div className="grid grid-cols-2 gap-4">
        {/* Format Comparison */}
        <ChartSection slug="comparacion-formato">
          <div>
            <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
              Rendimiento por formato
            </h3>
            <div className="rounded-lg border bg-card p-4 space-y-3">
              {formats.length > 0 ? (
                formats.map(fmt => <FormatRow key={fmt.formatType} format={fmt} />)
              ) : (
                <p className="py-4 text-center text-xs text-muted-foreground">
                  Sin datos de formatos disponibles
                </p>
              )}
            </div>
          </div>
        </ChartSection>

        {/* Video Retention (kept from existing implementation) */}
        <ChartSection slug="retencion-video"><div>
          <h3
            className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
            title="Cu\u00e1ntas personas ven tu video hasta cada punto. Ideal: >30% completa el video."
          >
            Retenci&oacute;n de video
          </h3>
          {hasRetention ? (
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-end gap-2 h-[180px] px-2">
                {[
                  { label: 'Play', value: retention.plays, pct: 100 },
                  {
                    label: '25%',
                    value: retention.p25,
                    pct: (retention.p25 / retention.plays) * 100,
                  },
                  {
                    label: '50%',
                    value: retention.p50,
                    pct: (retention.p50 / retention.plays) * 100,
                  },
                  {
                    label: '75%',
                    value: retention.p75,
                    pct: (retention.p75 / retention.plays) * 100,
                  },
                  {
                    label: '100%',
                    value: retention.p100,
                    pct: (retention.p100 / retention.plays) * 100,
                  },
                ].map((step, i) => (
                  <div key={step.label} className="flex-1 flex flex-col items-center gap-1">
                    <p className="text-[10px] font-semibold tabular-nums">
                      {formatCompact(step.value)}
                    </p>
                    <div
                      className={cn(
                        'w-full rounded-t',
                        i === 4
                          ? 'bg-emerald-500/50'
                          : i >= 3
                            ? 'bg-amber-500/40'
                            : 'bg-blue-500/50',
                      )}
                      style={{ height: `${Math.max(step.pct * 1.6, 4)}px` }}
                    />
                    <p className="text-[9px] text-muted-foreground">{step.label}</p>
                    {i > 0 && <p className="text-[8px] text-blue-400">{step.pct.toFixed(0)}%</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
              <p className="font-medium">Pr&oacute;ximamente</p>
              <p className="mt-1 text-xs">
                Gr&aacute;fico de retenci&oacute;n: Play &rarr; 25% &rarr; 50% &rarr; 75% &rarr; 100% completado.
              </p>
            </div>
          )}
        </div></ChartSection>
      </div>

      {/* ── Video KPIs (only if retention data exists) ────────────── */}
      {hasRetention && (
        <div className="grid grid-cols-4 gap-2.5">
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Video Views</p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.plays)}</p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Vistas 50%+</p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.p50)}</p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">Completados</p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.p100)}</p>
            <p className="text-[9px] text-emerald-500">
              {((retention.p100 / retention.plays) * 100).toFixed(0)}% completion rate
            </p>
          </div>
          <div className="rounded-lg border bg-card p-3">
            <p className="text-[10px] text-muted-foreground">
              <Eye className="mr-1 inline h-3 w-3" />
              Retenci&oacute;n 75%
            </p>
            <p className="text-xl font-bold tabular-nums mt-1">{formatCompact(retention.p75)}</p>
            <p className="text-[9px] text-muted-foreground">
              {((retention.p75 / retention.plays) * 100).toFixed(0)}% del total
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
