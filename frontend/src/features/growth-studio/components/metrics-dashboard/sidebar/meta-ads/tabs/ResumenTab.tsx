'use client';

import { useMemo, useState } from 'react';
import { Loader2, TrendingDown, TrendingUp } from 'lucide-react';

import { formatMoney } from '@/lib/format-money';
import { cn } from '@/lib/utils';
import { BenchmarkBadge } from '../../../channel-widgets/BenchmarkBadge';
import { ChartSection } from '../../shared/ChartSection';
import { MetaAdsMiniFunnel } from '../MetaAdsMiniFunnel';
import { InversionChart } from '../InversionChart';
import { MetaAdsHealthCheckPanel } from '../MetaAdsHealthCheckPanel';
import { OfferSegmenter } from '../OfferSegmenter';
import type { OfferSegmenterSelection } from '../OfferSegmenter';
import { UnassignedBanner } from '../UnassignedBanner';
import {
  useMetaHealthCheck,
  useMetricsByOffer,
} from '../../../../../api/offer-association-api';
import { useTenantLocale } from '@/features/tenant/context/tenant-locale-context';
import type {
  ChannelDashboardData,
  MetricKpiData,
  CampaignPerformanceData,
  CampaignRecommendation,
  MetaAdsDashboardTab,
  MetaAdsPeriod,
} from '../../../../../types/metrics';

interface ResumenTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  campaignData?: CampaignPerformanceData;
  period?: MetaAdsPeriod;
  onNavigateToTab?: (tab: MetaAdsDashboardTab) => void;
  onAssignCampaigns?: () => void;
}

const RESUMEN_KPIS = ['spend', 'ROAS', 'conversions', 'CPA', 'CTR', 'reach'];

/** Metrics that require Meta Pixel to report meaningful data. When value is 0, show "--" placeholder. */
const PIXEL_DEPENDENT_METRICS = new Set(['ROAS', 'CPA', 'CPL', 'conversions']);

function isPixelPlaceholder(metricName: string, value: number): boolean {
  return PIXEL_DEPENDENT_METRICS.has(metricName) && value === 0;
}

function formatKpiValue(value: number, unit: string, currency?: string, fallbackCurrency = 'USD'): string {
  if (unit === 'currency') return formatMoney(value, currency || fallbackCurrency);
  if (unit === 'percentage') return `${value.toFixed(2)}%`;
  if (unit === 'ratio') return `${value.toFixed(2)}x`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString('en-US');
}

const KPI_TOOLTIPS: Record<string, string> = {
  spend: 'Total invertido en Meta Ads durante el periodo seleccionado.',
  ROAS: 'ROAS = Por cada $1 invertido, cuánto recuperas. Ej: 3.2x = ganas $3.20 por cada $1.',
  conversions: 'Total de resultados (ventas, leads, etc.) generados por todas tus campañas.',
  CPA: 'CPA = Costo por cada resultado obtenido. Menor es mejor.',
  CTR: 'CTR = % de personas que ven tu anuncio y hacen clic. Más alto es mejor.',
  reach: 'Personas únicas que vieron tus anuncios. No es una suma diaria.',
};

function AlertCard({
  recommendation,
  onAction,
}: {
  recommendation: CampaignRecommendation;
  onAction?: () => void;
}) {
  const isCritical =
    recommendation.importance === 'HIGH' || recommendation.importance === 'CRITICAL';

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-3 flex items-start justify-between gap-3',
        isCritical ? 'border-l-2 border-l-red-500' : 'border-l-2 border-l-blue-500',
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'rounded-full p-1.5 mt-0.5 shrink-0',
            isCritical ? 'bg-red-500/10' : 'bg-blue-500/10',
          )}
        >
          {isCritical ? (
            <svg className="h-4 w-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          ) : (
            <TrendingUp className="h-4 w-4 text-blue-400" />
          )}
        </div>
        <div>
          <p className={cn('text-sm font-medium', isCritical ? 'text-red-300' : 'text-blue-300')}>
            {recommendation.title}
          </p>
          {recommendation.body && (
            <p className="text-xs text-muted-foreground mt-0.5">{recommendation.body}</p>
          )}
        </div>
      </div>
      {onAction && (
        <button
          onClick={onAction}
          className={cn(
            'shrink-0 rounded-md border px-3 py-1.5 text-xs',
            isCritical
              ? 'bg-red-500/10 border-red-500/30 text-red-400'
              : 'bg-blue-500/10 border-blue-500/30 text-blue-400',
          )}
        >
          {isCritical ? 'Ver en Campañas' : 'Ver detalle'}
        </button>
      )}
    </div>
  );
}

export function ResumenTab({
  data,
  isLoading,
  campaignData,
  period = '30d',
  onNavigateToTab,
  onAssignCampaigns,
}: ResumenTabProps) {
  const { currency: tenantCurrency } = useTenantLocale();
  const [selectedOfferId, setSelectedOfferId] =
    useState<OfferSegmenterSelection>('all');

  const { data: healthCheck, isLoading: isHealthLoading } = useMetaHealthCheck();
  const { data: metricsByOffer } = useMetricsByOffer(period);

  const unassignedCount = healthCheck?.unassignedTargets.length ?? 0;
  const hasUnassigned = unassignedCount > 0;
  const hasBranding = (metricsByOffer?.brandingOnly.targetCount ?? 0) > 0;

  const handleAssignClick = () => {
    if (onAssignCampaigns) {
      onAssignCampaigns();
    } else {
      onNavigateToTab?.('campanas');
    }
  };

  // Choose the primary expected metric when filtering by a specific offer.
  const selectedOfferMetrics = useMemo(() => {
    if (selectedOfferId === 'all' || selectedOfferId === 'unassigned' || selectedOfferId === 'branding') {
      return null;
    }
    return metricsByOffer?.offers.find(o => o.offerId === selectedOfferId) ?? null;
  }, [metricsByOffer, selectedOfferId]);

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

  const kpis = RESUMEN_KPIS
    .map(name => data.kpis.find(k => k.metricName === name))
    .filter((k): k is MetricKpiData => k != null);

  const hasTimeSeries = data.timeSeries.some(
    ts => ts.metricName === 'spend' && ts.dataPoints.length > 0,
  );

  return (
    <div className="space-y-6">
      {/* Health Check panel (diagnóstico de cuenta Meta) */}
      <ChartSection slug="health-check">
        <MetaAdsHealthCheckPanel
          data={healthCheck}
          isLoading={isHealthLoading}
          onAssignClick={handleAssignClick}
        />
      </ChartSection>

      {/* Unassigned banner (persistent prompt to assign) */}
      {hasUnassigned && (
        <UnassignedBanner
          count={unassignedCount}
          onAssignClick={handleAssignClick}
        />
      )}

      {/* 6 KPI cards */}
      <ChartSection slug="kpis">
        <div className="grid grid-cols-6 gap-2.5">
          {kpis.map(kpi => {
            const isPositive =
              kpi.deltaPct != null &&
              (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);
            return (
              <div
                key={kpi.metricName}
                className="rounded-lg border bg-card p-3 space-y-1"
                title={KPI_TOOLTIPS[kpi.metricName] ?? ''}
              >
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                  {kpi.displayName}
                </p>
                <p className="text-xl font-bold tabular-nums">
                  {isPixelPlaceholder(kpi.metricName, kpi.currentValue) ? (
                    <span title="Requiere Meta Pixel configurado">--</span>
                  ) : (
                    formatKpiValue(kpi.currentValue, kpi.unit, kpi.currency, tenantCurrency)
                  )}
                </p>
                {kpi.deltaPct != null && (
                  <span
                    className={cn(
                      'inline-flex items-center gap-0.5 text-[10px] font-medium',
                      isPositive ? 'text-emerald-600' : 'text-red-600',
                    )}
                  >
                    {isPositive ? (
                      <TrendingUp className="h-3 w-3" />
                    ) : (
                      <TrendingDown className="h-3 w-3" />
                    )}
                    {Math.abs(kpi.deltaPct).toFixed(1)}% vs ant.
                  </span>
                )}
                {kpi.benchmark && (
                  <BenchmarkBadge
                    value={kpi.currentValue}
                    benchmark={kpi.benchmark}
                    higherIsBetter={kpi.higherIsBetter}
                  />
                )}
              </div>
            );
          })}
        </div>
      </ChartSection>

      {/* Alerts / Recommendations */}
      {campaignData?.recommendations && campaignData.recommendations.length > 0 && (
        <ChartSection slug="alertas">
          <div className="space-y-2">
            {campaignData.recommendations.slice(0, 3).map((rec, i) => (
              <AlertCard
                key={rec.title ?? i}
                recommendation={rec}
                onAction={() => onNavigateToTab?.('campanas')}
              />
            ))}
          </div>
        </ChartSection>
      )}

      {/* Offer segmenter (multi-offer filter) */}
      {metricsByOffer && metricsByOffer.offers.length > 0 && (
        <ChartSection slug="segmentador-offers">
          <div className="space-y-2">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Filtrar por offer
            </p>
            <OfferSegmenter
              offers={metricsByOffer.offers}
              selectedOfferId={selectedOfferId}
              onSelect={setSelectedOfferId}
              hasUnassigned={hasUnassigned}
              hasBranding={hasBranding}
            />
            {selectedOfferMetrics && (
              <p className="text-[11px] text-muted-foreground">
                <strong className="text-foreground">{selectedOfferMetrics.offerName}</strong>
                {' '}· Métrica primaria: <strong className="text-foreground">{selectedOfferMetrics.primaryMetricName}</strong>
                {selectedOfferMetrics.primaryCostPerResult != null && (
                  <>
                    {' '}·{' '}
                    {formatMoney(
                      selectedOfferMetrics.primaryCostPerResult,
                      selectedOfferMetrics.currency || tenantCurrency,
                    )}
                  </>
                )}
                {selectedOfferMetrics.roas != null && (
                  <> · ROAS {selectedOfferMetrics.roas.toFixed(2)}x</>
                )}
              </p>
            )}
          </div>
        </ChartSection>
      )}

      {/* Inversión y Retorno — full width */}
      {hasTimeSeries && (
        <ChartSection slug="inversion-vs-resultados">
          <InversionChart timeSeries={data.timeSeries} />
        </ChartSection>
      )}

      {/* Embudo de conversión — separate section */}
      <ChartSection slug="embudo">
        <div className="rounded-lg border bg-card p-5 space-y-3">
          <h3 className="text-sm font-medium">Embudo de conversión</h3>
          <MetaAdsMiniFunnel steps={data.funnel.steps} />
        </div>
      </ChartSection>
    </div>
  );
}
