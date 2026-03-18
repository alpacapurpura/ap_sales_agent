'use client';

import { useNurtureDetail } from '../../../hooks/useNurtureDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const NUTRICION_STAGE: StageSummary = {
  id: 'NUTRICION',
  order: 2,
  label: 'Nutricion',
  description: 'MQLs calificados por retargeting y automatizaciones',
  mainKpi: { label: 'MQLs', value: 0 },
  secondaryKpi: { label: 'conversion', value: 0, unit: '%' },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

interface NurtureDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
  onConfigure?: (slug: string, name: string) => void;
}

export function NurtureDetail({ onMetricClick, onConfigure }: NurtureDetailProps) {
  const { data, isLoading, error, refetch } = useNurtureDetail();

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
    return <DetailEmpty stage={NUTRICION_STAGE} />;
  }

  const { headerKpis, miniFunnel } = data;

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
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">TOTAL MQLs</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.totalMqls.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">CONVERSION</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.conversionRate.toFixed(1)}%
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">COSTO POR MQL</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
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
        stageId="NUTRICION"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Automatizacion"
        totals={data.automation.totals}
        channels={data.automation.channels}
        groupType="automation"
        defaultOpen
        stageId="NUTRICION"
        onMetricClick={onMetricClick}
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          totals={{}}
          channels={data.available.channels}
          groupType="available"
          defaultOpen={false}
          stageId="NUTRICION"
          onMetricClick={onMetricClick}
          onConfigure={onConfigure}
        />
      )}
    </div>
  );
}
