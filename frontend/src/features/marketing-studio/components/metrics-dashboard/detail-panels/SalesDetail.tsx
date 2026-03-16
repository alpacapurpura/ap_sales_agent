'use client';

import { AlertTriangle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { useSalesDetail } from '../../../hooks/useSalesDetail';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { RevenueGroupHeader } from '../channel-widgets/RevenueGroupHeader';
import { TierGroup } from '../channel-widgets/TierGroup';
import type { SalesBottleneck, RevenueGroupData } from '../../../types/metrics';

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

const GROUP_SUBTITLES: Record<string, string> = {
  adquisicion: 'Clientes nuevos (CONVERSION)',
  expansion: 'Ventas recurrentes y upsell (EXPANSION)',
};

function SalesBottleneckBanner({ bottleneck }: { bottleneck: SalesBottleneck }) {
  const { severity, message, tip } = bottleneck;

  const bgColor = severity === 'critical'
    ? 'bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-800'
    : 'bg-yellow-50 border-yellow-200 dark:bg-yellow-950/20 dark:border-yellow-800';
  const textColor = severity === 'critical'
    ? 'text-red-800 dark:text-red-200'
    : 'text-yellow-800 dark:text-yellow-200';

  return (
    <div className={`rounded-lg border p-3 ${bgColor}`} role="alert">
      <div className="flex items-center gap-2">
        <AlertTriangle className={`h-4 w-4 ${textColor}`} />
        <span className={`text-sm font-semibold ${textColor}`}>{message}</span>
      </div>
      <p className="text-xs text-muted-foreground mt-1">{tip}</p>
    </div>
  );
}

function RevenueSection({ group }: { group: RevenueGroupData }) {
  const nonEmptyTiers = group.tiers.filter((t) => t.offers.length > 0);
  if (nonEmptyTiers.length === 0) return null;

  return (
    <div>
      <RevenueGroupHeader
        groupLabel={group.groupLabel}
        subtitle={GROUP_SUBTITLES[group.groupKey] ?? ''}
        totalRevenue={group.totalRevenue}
        totalRevenueUsd={group.totalRevenueUsd}
        currency={group.currency}
        customerCount={group.customerCount}
        revenuePercentage={group.revenuePercentage}
      />
      {nonEmptyTiers.map((tier) => (
        <TierGroup
          key={tier.tierKey}
          tierKey={tier.tierKey}
          tierLabel={tier.tierLabel}
          offers={tier.offers}
        />
      ))}
    </div>
  );
}

export function SalesDetail() {
  const { data, isLoading, error } = useSalesDetail();

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
        No se pudieron cargar los datos de ventas. Verifica tu conexion e intenta nuevamente.
      </div>
    );
  }

  const { headerKpis, miniFunnel, adquisicion, expansion, bottlenecks } = data;

  // Check if there are no offers at all
  const hasAdqOffers = adquisicion.tiers.some((t) => t.offers.length > 0);
  const hasExpOffers = expansion.tiers.some((t) => t.offers.length > 0);

  if (!hasAdqOffers && !hasExpOffers) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin ofertas configuradas</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Configura tu Offer Ladder para ver ventas por producto. Tu panel de ventas se llenara
          automaticamente cuando registres tus primeras transacciones.
        </p>
        <a href="/offer-studio" className="text-xs text-primary underline mt-3">
          Ir a Offer Studio
        </a>
      </div>
    );
  }

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
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">REVENUE TOTAL</span>
          <span className="text-xl font-semibold tabular-nums">
            {formatDualCurrency(headerKpis.totalRevenue, headerKpis.currency, headerKpis.totalRevenueUsd)}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">NUEVOS CLIENTES</span>
          <span className="text-xl font-semibold tabular-nums">{headerKpis.newCustomers.toLocaleString('es-ES')}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">CAC</span>
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.cac != null
              ? `${new Intl.NumberFormat('es-MX', { style: 'currency', currency: headerKpis.currency, minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(headerKpis.cac)}${headerKpis.cacIncomplete ? '*' : ''}`
              : '--'}
          </span>
          {headerKpis.cacIncomplete && (
            <span className="text-[10px] text-muted-foreground">
              Costos incompletos -- configura en Growth Settings
            </span>
          )}
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2 px-3">
          {bottlenecks.map((b) => (
            <SalesBottleneckBanner key={b.type} bottleneck={b} />
          ))}
        </div>
      )}

      {/* Revenue Groups */}
      <RevenueSection group={adquisicion} />
      <RevenueSection group={expansion} />
    </div>
  );
}
