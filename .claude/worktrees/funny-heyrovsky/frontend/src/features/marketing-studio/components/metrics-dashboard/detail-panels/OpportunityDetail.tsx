'use client';

import { useOpportunityDetail } from '../../../hooks/useOpportunityDetail';
import { ChannelGroup } from '../channel-widgets/ChannelGroup';
import { MiniFunnel } from '../channel-widgets/MiniFunnel';
import { BottleneckBanner } from './BottleneckBanner';
import DetailSkeleton from '../ui/DetailSkeleton';
import DetailEmpty from '../ui/DetailEmpty';
import DetailError from '../ui/DetailError';
import type { MetricClickData, StageSummary } from '../../../types/metrics';

const OPORTUNIDAD_STAGE: StageSummary = {
  id: 'OPORTUNIDAD',
  order: 3,
  label: 'Oportunidad',
  description: 'SQLs listos para decision de compra',
  mainKpi: { label: 'SQLs', value: 0 },
  secondaryKpi: { label: 'conversion', value: 0, unit: '%' },
  hasDetail: true,
};

function formatLastUpdated(isoDate: string): string {
  const d = new Date(isoDate);
  return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

interface OpportunityDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export function OpportunityDetail({ onMetricClick }: OpportunityDetailProps) {
  const { data, isLoading, error, refetch } = useOpportunityDetail();

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
    return <DetailEmpty stage={OPORTUNIDAD_STAGE} />;
  }

  const { headerKpis, miniFunnel, checkout, paymentLinks, qualification, bottlenecks, available } = data;

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
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">TOTAL SQLs</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.totalSqls.toLocaleString('es-ES')}
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">CONVERSION MQL → SQL</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.conversionRate.toFixed(1)}%
          </span>
        </div>
        <div className="flex flex-col bg-muted/30 rounded-lg p-3">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide">COSTO POR SQL</span>
          <span className="text-xl sm:text-2xl font-semibold tabular-nums mt-1">
            {headerKpis.costPerSql != null ? `$${headerKpis.costPerSql.toLocaleString('es-ES')}` : '---'}
          </span>
        </div>
      </div>

      {/* MiniFunnel */}
      <MiniFunnel data={miniFunnel} />

      {/* Bottleneck Banners — only show warning/critical */}
      {bottlenecks.filter(b => b.severity !== 'normal').length > 0 && (
        <div className="space-y-2">
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
        stageId="OPORTUNIDAD"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Links de Pago"
        groupType="payment_links"
        channels={paymentLinks.channels}
        totals={paymentLinks.totals}
        defaultOpen
        stageId="OPORTUNIDAD"
        onMetricClick={onMetricClick}
      />
      <ChannelGroup
        title="Calificacion"
        groupType="qualification"
        channels={qualification.channels}
        totals={qualification.totals}
        defaultOpen
        stageId="OPORTUNIDAD"
        onMetricClick={onMetricClick}
      />

      {/* Available Channels */}
      {available && available.channels.length > 0 && (
        <ChannelGroup
          title="Canales Disponibles"
          groupType="available"
          channels={available.channels}
          totals={{}}
          defaultOpen={false}
          stageId="OPORTUNIDAD"
          onMetricClick={onMetricClick}
        />
      )}
    </div>
  );
}
