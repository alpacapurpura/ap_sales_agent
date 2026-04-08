'use client';

import { memo, useState, type ReactNode } from 'react';
import { ExternalLink, Loader2, type LucideIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from '@/components/ui/detail-panel';
import { useChannelDashboard } from '../../../../hooks/useChannelDashboard';
import type {
  ChannelDashboardData,
  ChannelMetric,
  MetaAdsPeriod,
} from '../../../../types/metrics';
import { PeriodSelector } from './PeriodSelector';
import { HeroKpiGrid } from './HeroKpiGrid';
import { MetaAdsMiniFunnel } from '../meta-ads/MetaAdsMiniFunnel';

interface FormatOptions {
  /** Number of decimal places for percentage values (default: 2) */
  percentDecimals?: number;
}

export interface ChannelOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  /** Lucide icon component to display in header */
  icon: LucideIcon;
  /** Tailwind text color class for the icon (e.g. 'text-pink-500') */
  iconColor: string;
  /** Ordered list of metric names for the hero KPI grid */
  heroMetrics: string[];
  /** Prefix for SVG gradient IDs to avoid collisions */
  gradientPrefix?: string;
  /** Override channel slug used for dashboard API (e.g. 'email-nurture') */
  dashboardSlug?: string;
  /** Show MetricInfoCard tooltips on KPIs */
  showMetricInfoCard?: boolean;
  /** Formatting options for KPI values */
  formatOptions?: FormatOptions;
  /** Channel-specific widgets rendered below the funnel */
  children?: (data: ChannelDashboardData) => ReactNode;
}

export const ChannelOverviewPanel = memo(function ChannelOverviewPanel({
  channel,
  onClose,
  onExpand,
  icon: Icon,
  iconColor,
  heroMetrics,
  gradientPrefix = 'ch',
  dashboardSlug,
  showMetricInfoCard = true,
  formatOptions,
  children,
}: ChannelOverviewPanelProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>('30d');
  const { data, isLoading } = useChannelDashboard(
    dashboardSlug ?? channel.slug,
    period,
  );

  return (
    <div className="flex h-full flex-col">
      <DetailPanelHeader className="flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={`h-5 w-5 ${iconColor}`} />
          <DetailPanelTitle>{channel.name}</DetailPanelTitle>
        </div>
        <DetailPanelClose onClose={onClose} />
      </DetailPanelHeader>

      <div className="flex items-center justify-between px-4 py-2 border-b">
        <PeriodSelector value={period} onChange={setPeriod} />
        {onExpand && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onExpand}
            className="gap-1.5 text-xs"
            aria-label="Dashboard completo"
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
            <HeroKpiGrid
              kpis={data.kpis}
              timeSeries={data.timeSeries}
              heroMetrics={heroMetrics}
              gradientPrefix={gradientPrefix}
              showMetricInfoCard={showMetricInfoCard}
              formatOptions={formatOptions}
            />
            <MetaAdsMiniFunnel steps={data.funnel.steps} />
            {children?.(data)}
          </>
        ) : (
          <div className="text-center py-12 text-sm text-muted-foreground">
            No hay datos para el periodo seleccionado
          </div>
        )}
      </div>
    </div>
  );
});

ChannelOverviewPanel.displayName = 'ChannelOverviewPanel';
