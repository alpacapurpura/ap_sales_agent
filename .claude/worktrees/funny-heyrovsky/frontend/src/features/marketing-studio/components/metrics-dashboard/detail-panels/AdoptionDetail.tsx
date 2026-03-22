'use client';

import { useAdoptionDetail } from '../../../hooks/useAdoptionDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { HealthBar } from '../channel-widgets/HealthBar';
import { OfferHealthCard } from '../channel-widgets/OfferHealthCard';
import { BottleneckBanner } from './BottleneckBanner';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const ADOPCION_STAGE: StageSummary = {
  id: 'ADOPCION',
  order: 5,
  label: 'Adopcion',
  description: 'Salud y activacion de clientes existentes',
  mainKpi: { label: 'salud %', value: 0, unit: '%' },
  secondaryKpi: { label: 'activos', value: 0 },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

function formatDualCurrency(amount: number, currency: string, usdAmount: number | null): string {
  const fmt = new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  const main = fmt.format(amount);

  if (currency === 'USD') return main;
  if (usdAmount != null) {
    const usdFmt = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    });
    return `${main} (~${usdFmt.format(usdAmount)} USD)`;
  }
  return main;
}

interface AdoptionDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export function AdoptionDetail({ onMetricClick }: AdoptionDetailProps) {
  const { data, isLoading, error, refetch } = useAdoptionDetail();

  if (isLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (error) {
    return (
      <DetailError
        error={error instanceof Error ? error : new Error('Error desconocido')}
        onRetry={() => { void refetch(); }}
        lastData={data}
      />
    );
  }

  if (!data) {
    return <DetailEmpty stage={ADOPCION_STAGE} />;
  }

  // Empty state
  if (data.offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin clientes registrados</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Cuando completes tus primeras ventas, aqui veras como tus clientes usan tu producto o servicio.
        </p>
        <span className="text-xs text-primary underline mt-3 cursor-pointer">
          Ir a Ventas
        </span>
      </div>
    );
  }

  const { headerKpis, miniFunnel, offers, bottlenecks } = data;

  const healthColor = headerKpis.healthPct >= 70
    ? 'text-emerald-600 dark:text-emerald-400'
    : 'text-yellow-600 dark:text-yellow-400';

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground italic">
          Actualizado: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Primary Header KPIs — responsive 3-column grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">CLIENTES ACTIVOS</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.activeCustomers.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">CLIENTES INACTIVOS</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.inactiveCustomers.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">SALUD DEL CLIENTE</span>
          <span className={`text-xl sm:text-2xl font-semibold tabular-nums mt-1 ${healthColor}`}>
            {headerKpis.healthPct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Secondary KPIs */}
      <div className="flex items-center gap-4 sm:gap-6 flex-wrap">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">TIEMPO DE ACTIVACION</span>
          <span className="text-sm font-semibold tabular-nums">
            {headerKpis.avgTtvDays != null ? `${Math.round(headerKpis.avgTtvDays)} dias` : '--'}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">DEVOLUCIONES</span>
          <span className="text-sm font-semibold tabular-nums">
            {headerKpis.refundCount > 0
              ? `${headerKpis.refundCount} (${formatDualCurrency(headerKpis.refundAmount, headerKpis.refundCurrency, headerKpis.refundAmountUsd)})`
              : '0'}
          </span>
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2">
          {bottlenecks.map((b) => (
            <BottleneckBanner
              key={`${b.type}-${b.metricLabel}`}
              bottleneck={{
                type: b.type as 'abandoned_cart' | 'meeting_no_show',
                metricLabel: b.metricLabel,
                currentRate: b.currentRate,
                severity: b.severity,
                threshold: b.threshold,
                tip: b.tip,
              }}
            />
          ))}
        </div>
      )}

      {/* Health Bar */}
      <HealthBar
        activeCount={headerKpis.activeCustomers}
        inactiveCount={headerKpis.inactiveCustomers}
      />

      {/* Offer Health Cards */}
      <div className="space-y-2">
        {offers.map((offer) => (
          <div
            key={offer.offerId}
            className={onMetricClick ? 'cursor-pointer hover:opacity-90 transition-opacity duration-100' : ''}
            onClick={onMetricClick ? () => onMetricClick({
              stageId: 'ADOPCION',
              channelSlug: offer.offerId,
              metricName: 'health_pct',
              currentValue: offer.healthPct,
            }) : undefined}
            role={onMetricClick ? 'button' : undefined}
            tabIndex={onMetricClick ? 0 : undefined}
            onKeyDown={onMetricClick ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                onMetricClick({
                  stageId: 'ADOPCION',
                  channelSlug: offer.offerId,
                  metricName: 'health_pct',
                  currentValue: offer.healthPct,
                });
              }
            } : undefined}
          >
            <OfferHealthCard offer={offer} />
          </div>
        ))}
      </div>
    </div>
  );
}
