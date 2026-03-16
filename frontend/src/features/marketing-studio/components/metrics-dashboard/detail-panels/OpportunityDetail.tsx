'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useOpportunityDetail } from '../../../hooks/useOpportunityDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { BottleneckBanner } from './BottleneckBanner';

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

export function OpportunityDetail() {
  const { data, isLoading, error } = useOpportunityDetail();

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
        No se pudieron cargar los datos de oportunidad. Verifica tu conexion e intenta nuevamente.
      </div>
    );
  }

  const { headerKpis, miniFunnel, checkout, paymentLinks, qualification, bottlenecks, available } = data;

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
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">TOTAL SQLs</span>
          <span className="text-xl font-semibold tabular-nums">{headerKpis.totalSqls.toLocaleString('es-ES')}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">CONVERSION</span>
          <span className="text-xl font-semibold tabular-nums">{headerKpis.conversionRate.toFixed(1)}%</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">COSTO POR SQL</span>
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.costPerSql != null ? `$${headerKpis.costPerSql.toLocaleString('es-ES')}` : '---'}
          </span>
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners */}
      {bottlenecks.filter(b => b.severity !== 'normal').length > 0 && (
        <div className="space-y-2 px-3">
          {bottlenecks
            .filter(b => b.severity !== 'normal')
            .map((b) => (
              <BottleneckBanner key={b.type} bottleneck={b} />
            ))}
        </div>
      )}

      {/* Channel Groups */}
      <ChannelGroup
        title="Checkout"
        groupType="checkout"
        channels={checkout.channels}
        totals={checkout.totals}
        defaultOpen
      />
      <ChannelGroup
        title="Links de Pago"
        groupType="payment_links"
        channels={paymentLinks.channels}
        totals={paymentLinks.totals}
        defaultOpen
      />
      <ChannelGroup
        title="Calificacion"
        groupType="qualification"
        channels={qualification.channels}
        totals={qualification.totals}
        defaultOpen
      />

      {/* Available Channels */}
      {available && available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          groupType="available"
          channels={available.channels}
          totals={{}}
          defaultOpen={false}
        />
      )}
    </div>
  );
}
