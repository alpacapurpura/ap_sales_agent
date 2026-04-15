"use client";

import { ExternalLink, Loader2, RefreshCw, type LucideIcon } from "lucide-react";
import { memo, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import {
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatTenantDateTime } from "@/lib/format-date";
import { cn } from "@/lib/utils";

import { useChannelDashboard } from "../../../../hooks/useChannelDashboard";
import { useSyncChannel } from "../../../../hooks/useSyncChannel";
import { MetaAdsMiniFunnel } from "../meta-ads/MetaAdsMiniFunnel";

import { HeroKpiGrid } from "./HeroKpiGrid";
import { PeriodSelector } from "./PeriodSelector";

import type { ChannelDashboardData, ChannelMetric, MetaAdsPeriod } from "../../../../types/metrics";

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
  gradientPrefix = "ch",
  dashboardSlug,
  showMetricInfoCard = true,
  formatOptions,
  children,
}: ChannelOverviewPanelProps) {
  const { timezone } = useTenantLocale();
  const [period, setPeriod] = useState<MetaAdsPeriod>("30d");
  const slug = dashboardSlug ?? channel.slug;
  const { data, isLoading } = useChannelDashboard(slug, period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel(slug);

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
        <div className="flex items-center gap-2">
          {channel.lastUpdated && (
            <span className="text-[10px] text-muted-foreground">
              Sync: {formatTenantDateTime(channel.lastUpdated, timezone)}
            </span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => sync()}
            disabled={isSyncing || cooldownMinutes > 0}
            title={
              cooldownMinutes > 0
                ? `Disponible en ${Math.ceil(cooldownMinutes)} min`
                : "Sincronizar"
            }
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isSyncing && "animate-spin")} />
          </Button>
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

ChannelOverviewPanel.displayName = "ChannelOverviewPanel";
