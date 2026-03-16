'use client';

import { useAttractionDetail } from '../../../hooks/useAttractionDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const ATRACCION_STAGE: StageSummary = {
  id: 'ATRACCION',
  order: 0,
  label: 'Atraccion',
  description: 'Trafico y alcance de canales de marketing',
  mainKpi: { label: 'visitantes', value: 0 },
  secondaryKpi: { label: 'canales activos', value: 0 },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }) + ', ' + d.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

interface AttractionDetailProps {
  /** Callback when user clicks a metric value to open the action sidebar */
  onMetricClick?: (metric: MetricClickData) => void;
}

export function AttractionDetail({ onMetricClick }: AttractionDetailProps) {
  const { data, isLoading, error, refetch } = useAttractionDetail();

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
    return <DetailEmpty stage={ATRACCION_STAGE} />;
  }

  // Compute header KPIs from group totals
  const allGroups = [data.organicSocial, data.ga4Search, data.paid, data.outbound];
  const totalVisitors = allGroups.reduce((sum, g) => sum + (g.totals.visitors ?? g.totals.totalVisitors ?? 0), 0);
  const totalReach = allGroups.reduce((sum, g) => sum + (g.totals.reach ?? 0), 0);
  const totalSpend = allGroups.reduce((sum, g) => sum + (g.totals.spend ?? 0), 0);
  const connectedChannels = allGroups.flatMap(g => g.channels.filter(c => c.connected)).length;

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
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">VISITANTES TOTALES</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {totalVisitors > 0 ? totalVisitors.toLocaleString('es-ES') : '---'}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">ALCANCE TOTAL</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {totalReach > 0 ? totalReach.toLocaleString('es-ES') : '---'}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
            {totalSpend > 0 ? 'GASTO TOTAL' : 'CANALES ACTIVOS'}
          </span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {totalSpend > 0
              ? `$${totalSpend.toLocaleString('es-ES', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
              : `${connectedChannels}`}
          </span>
        </div>
      </div>

      {/* Channel Groups */}
      <ChannelGroup
        title="Redes Sociales"
        totals={data.organicSocial.totals}
        channels={data.organicSocial.channels}
        groupType="organic_social"
        defaultOpen
        stageId="ATRACCION"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Busqueda"
        totals={data.ga4Search.totals}
        channels={data.ga4Search.channels}
        groupType="ga4_search"
        defaultOpen
        stageId="ATRACCION"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Publicidad Pagada"
        totals={data.paid.totals}
        channels={data.paid.channels}
        groupType="paid"
        defaultOpen
        stageId="ATRACCION"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Contacto Directo"
        totals={data.outbound.totals}
        channels={data.outbound.channels}
        groupType="outbound"
        defaultOpen
        stageId="ATRACCION"
        onMetricClick={onMetricClick}
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          totals={{}}
          channels={data.available.channels}
          groupType="available"
          defaultOpen={false}
          stageId="ATRACCION"
          onMetricClick={onMetricClick}
        />
      )}
    </div>
  );
}
