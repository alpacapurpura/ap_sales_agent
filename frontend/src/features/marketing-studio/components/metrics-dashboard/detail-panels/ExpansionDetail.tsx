'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useExpansionDetail } from '../../../hooks/useExpansionDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { KpiTooltip } from '../channel-widgets/KpiTooltip';
import { ExpansionGroup } from '../channel-widgets/ExpansionGroup';
import { BottleneckBanner } from './BottleneckBanner';

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

export function ExpansionDetail() {
  const { data, isLoading, error } = useExpansionDetail();

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No se pudieron cargar los datos de expansion. Verifica tu conexion e intenta nuevamente.
      </div>
    );
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
    <div className="space-y-2">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground px-3 pb-1">
          Ultima actualizacion: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Header KPIs */}
      <div className="flex items-center gap-6 px-3 py-2">
        <div className="flex flex-col">
          <KpiTooltip
            label="INGRESO RECURRENTE NETO"
            hint="Dinero que recibes cada mes de suscripciones activas, despues de restar cancelaciones"
          />
          <span className="text-xl font-semibold tabular-nums">
            {formatDualCurrency(headerKpis.netMrr, headerKpis.currency, headerKpis.netMrrUsd)}
          </span>
        </div>
        <div className="flex flex-col">
          <KpiTooltip
            label="VALOR PROMEDIO POR CLIENTE"
            hint="Cuanto dinero ha generado en promedio cada cliente desde su primera compra"
          />
          <span className="text-xl font-semibold tabular-nums">
            {formatDualCurrency(headerKpis.avgLtv, headerKpis.currency, headerKpis.avgLtvUsd)}
          </span>
        </div>
        <div className="flex flex-col">
          <KpiTooltip
            label="TASA DE CANCELACION"
            hint="Porcentaje de suscriptores que cancelaron en este periodo. Menos de 5% es saludable"
          />
          <span className={`text-xl font-semibold tabular-nums ${churnColor}`}>
            {headerKpis.churnRatePct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2 px-3">
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
