'use client';

import { useState } from 'react';
import { ExternalLink, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from '@/components/ui/detail-panel';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import type { ChannelMetric, MetaAdsPeriod } from '../../../../types/metrics';
import { MetaAdsPeriodSelector } from './MetaAdsPeriodSelector';
import { MetaAdsHeroKpiGrid } from './MetaAdsHeroKpiGrid';
import { MetaAdsMiniFunnel } from './MetaAdsMiniFunnel';
import { ReachFrequencySection } from './ReachFrequencySection';

interface MetaAdsOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
}

export function MetaAdsOverviewPanel({
  channel,
  onClose,
  onExpand,
}: MetaAdsOverviewPanelProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const { data, isLoading } = useChannelDashboard(channel.slug, period);

  return (
    <div className="flex h-full flex-col">
      <DetailPanelHeader className="flex-row items-center justify-between">
        <DetailPanelTitle>{channel.name}</DetailPanelTitle>
        <DetailPanelClose onClose={onClose} />
      </DetailPanelHeader>

      <div className="flex items-center justify-between px-4 py-2 border-b">
        <MetaAdsPeriodSelector value={period} onChange={setPeriod} />
        {onExpand && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onExpand}
            className="gap-1.5 text-xs"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Dashboard completo
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : data ? (
          <>
            <MetaAdsHeroKpiGrid kpis={data.kpis} timeSeries={data.timeSeries} />
            <MetaAdsMiniFunnel steps={data.funnel.steps} />
            <ReachFrequencySection
              kpis={data.kpis}
              frequencyAlert={data.frequencyAlert}
            />
          </>
        ) : (
          <div className="text-center py-12 text-sm text-muted-foreground">
            No hay datos para el periodo seleccionado
          </div>
        )}
      </div>
    </div>
  );
}
