'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { useNurtureDetail } from '../../../hooks/useNurtureDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

export function NurtureDetail() {
  const { data, isLoading, error } = useNurtureDetail();

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
        No se pudieron cargar los datos de nutricion. Verifica tu conexion e intenta nuevamente.
      </div>
    );
  }

  const { headerKpis, miniFunnel } = data;

  return (
    <div className="space-y-2">
      {data.lastUpdated && (
        <p className="text-xs text-muted-foreground px-3 pb-1">
          Ultima actualizacion: {formatLastUpdated(data.lastUpdated)}
        </p>
      )}

      {/* Panel Header KPIs */}
      <div className="flex items-center gap-6 px-3 py-2">
        <div className="flex flex-col">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">TOTAL MQLs</span>
          <span className="text-xl font-semibold tabular-nums">{headerKpis.totalMqls.toLocaleString('es-ES')}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">CONVERSION</span>
          <span className="text-xl font-semibold tabular-nums">{headerKpis.conversionRate.toFixed(1)}%</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">COSTO POR MQL</span>
          <span className="text-xl font-semibold tabular-nums">
            {headerKpis.costPerMql !== null ? `$${headerKpis.costPerMql.toFixed(2)}` : '---'}
          </span>
        </div>
      </div>

      {/* Mini Funnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Channel Groups */}
      <ChannelGroup
        title="Retargeting Omnichannel"
        totals={data.retargeting.totals}
        channels={data.retargeting.channels}
        groupType="retargeting"
        defaultOpen
      />
      <ChannelGroup
        title="Automatizacion"
        totals={data.automation.totals}
        channels={data.automation.channels}
        groupType="automation"
        defaultOpen
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          totals={{}}
          channels={data.available.channels}
          groupType="available"
          defaultOpen={false}
        />
      )}
    </div>
  );
}
