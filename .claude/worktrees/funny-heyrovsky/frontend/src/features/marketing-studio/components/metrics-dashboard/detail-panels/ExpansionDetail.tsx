'use client';

import { useExpansionDetail } from '../../../hooks/useExpansionDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { KpiTooltip } from '../channel-widgets/KpiTooltip';
import { ExpansionGroup } from '../channel-widgets/ExpansionGroup';
import { BottleneckBanner } from './BottleneckBanner';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const EXPANSION_STAGE: StageSummary = {
  id: 'EXPANSION',
  order: 6,
  label: 'Expansion',
  description: 'Ingreso recurrente, upsell y cancelaciones',
  mainKpi: { label: 'net MRR', value: 0, unit: '$' },
  secondaryKpi: { label: 'churn %', value: 0, unit: '%' },
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

interface ExpansionDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export function ExpansionDetail({ onMetricClick }: ExpansionDetailProps) {
  const { data, isLoading, error, refetch } = useExpansionDetail();

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
    return <DetailEmpty stage={EXPANSION_STAGE} />;
  }

  const { headerKpis, miniFunnel, retencion, crecimiento, cancelaciones, bottlenecks } = data;

  // Empty state: all three groups have no transactions
  if (retencion.totalCount === 0 && crecimiento.totalCount === 0 && cancelaciones.totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin datos de retencion</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Cuando tus clientes renueven o compren productos adicionales, aqui veras como crece tu ingreso recurrente.
        </p>
      </div>
    );
  }

  const churnColor = headerKpis.churnRatePct > 5
    ? 'text-red-600 dark:text-red-400'
    : headerKpis.churnRatePct > 3
      ? 'text-yellow-600 dark:text-yellow-400'
      : '';

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground italic">
          Actualizado: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Header KPIs — responsive 3-column grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          className={`flex flex-col bg-muted/30 rounded-lg p-3 ${onMetricClick ? 'cursor-pointer hover:bg-muted/50 transition-colors duration-100' : ''}`}
          onClick={onMetricClick ? () => onMetricClick({
            stageId: 'EXPANSION',
            channelSlug: 'mrr',
            metricName: 'net_mrr',
            currentValue: headerKpis.netMrr,
            currency: headerKpis.currency,
          }) : undefined}
          role={onMetricClick ? 'button' : undefined}
          tabIndex={onMetricClick ? 0 : undefined}
        >
          <KpiTooltip
            label="INGRESO RECURRENTE NETO"
            hint="Dinero que recibes cada mes de suscripciones activas, despues de restar cancelaciones"
          />
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {formatDualCurrency(headerKpis.netMrr, headerKpis.currency, headerKpis.netMrrUsd)}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <KpiTooltip
            label="VALOR PROMEDIO POR CLIENTE"
            hint="Cuanto dinero ha generado en promedio cada cliente desde su primera compra"
          />
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {formatDualCurrency(headerKpis.avgLtv, headerKpis.currency, headerKpis.avgLtvUsd)}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <KpiTooltip
            label="TASA DE CANCELACION"
            hint="Porcentaje de suscriptores que cancelaron en este periodo. Menos de 5% es saludable"
          />
          <span className={`text-xl sm:text-2xl font-semibold tabular-nums mt-1 ${churnColor}`}>
            {headerKpis.churnRatePct.toFixed(1)}%
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
              key={b.type}
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

      {/* Three Groups */}
      <ExpansionGroup group={retencion} />
      <ExpansionGroup group={crecimiento} />
      <ExpansionGroup group={cancelaciones} variant="churn" />
    </div>
  );
}
