'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useAdoptionDetail } from '../../../hooks/useAdoptionDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { HealthBar } from '../channel-widgets/HealthBar';
import { OfferHealthCard } from '../channel-widgets/OfferHealthCard';
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

export function AdoptionDetail() {
  const { data, isLoading, error } = useAdoptionDetail();

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
        No se pudieron cargar los datos de adopcion. Verifica tu conexion e intenta nuevamente.
      </div>
    );
  }

  // Empty state
  if (data.offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin clientes registrados</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Cuando completes tus primeras ventas, aqui veras como tus clientes usan tu producto o servicio.
        </p>
        <span className="text-xs text-primary underline mt-3">
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
    <div className="space-y-2">
      {/* Timestamp */}
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground px-3 pb-1">
          Ultima actualizacion: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Primary Header KPIs */}
      <div className="flex items-center gap-6 px-3 py-2">
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">CLIENTES ACTIVOS</span>
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.activeCustomers.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">CLIENTES INACTIVOS</span>
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.inactiveCustomers.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">SALUD DEL CLIENTE</span>
          <span className={`text-xl font-semibold tabular-nums ${healthColor}`}>
            {headerKpis.healthPct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Secondary KPIs */}
      <div className="flex items-center gap-6 px-3">
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
        <div className="space-y-2 px-3">
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

      {/* Offer Cards */}
      <div className="space-y-2 px-3">
        {offers.map((offer) => (
          <OfferHealthCard key={offer.offerId} offer={offer} />
        ))}
      </div>
    </div>
  );
}
