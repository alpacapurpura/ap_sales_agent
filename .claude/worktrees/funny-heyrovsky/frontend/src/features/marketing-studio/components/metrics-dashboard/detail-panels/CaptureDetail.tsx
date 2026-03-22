'use client';

import { useCaptureDetail } from '../../../hooks/useCaptureDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const CAPTURA_STAGE: StageSummary = {
  id: 'CAPTURA',
  order: 1,
  label: 'Captura',
  description: 'Leads generados desde formularios y agentes conversacionales',
  mainKpi: { label: 'leads', value: 0 },
  secondaryKpi: { label: 'conversion', value: 0, unit: '%' },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

interface CaptureDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export function CaptureDetail({ onMetricClick }: CaptureDetailProps) {
  const { data, isLoading, error, refetch } = useCaptureDetail();

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
    return <DetailEmpty stage={CAPTURA_STAGE} />;
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
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">TOTAL LEADS</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.totalLeads.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">CONVERSION</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.conversionRate.toFixed(1)}%
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">COSTO POR LEAD</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.costPerLead !== null ? `$${headerKpis.costPerLead.toFixed(2)}` : '---'}
          </span>
        </div>
      </div>

      {/* Mini Funnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Channel Groups */}
      <ChannelGroup
        title="Infraestructura Web"
        totals={data.webInfrastructure.totals}
        channels={data.webInfrastructure.channels}
        groupType="web_infrastructure"
        defaultOpen
        stageId="CAPTURA"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Agente AI Conversacional"
        totals={data.aiAgent.totals}
        channels={data.aiAgent.channels}
        groupType="ai_agent"
        defaultOpen
        stageId="CAPTURA"
        onMetricClick={onMetricClick}
      />
      {data.available && data.available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          totals={{}}
          channels={data.available.channels}
          groupType="available"
          defaultOpen={false}
          stageId="CAPTURA"
          onMetricClick={onMetricClick}
        />
      )}
    </div>
  );
}
