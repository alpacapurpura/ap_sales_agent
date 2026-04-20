"use client";

import { ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import { useCampaignPerformance } from "../../../../api/campaigns-api";
import { useChannelDashboard } from "../../../../hooks/use-channel-dashboard";

import { MetaAdsHeroKpiGrid } from "./MetaAdsHeroKpiGrid";
import { MetaAdsMiniFunnel } from "./MetaAdsMiniFunnel";
import { MetaAdsPeriodSelector } from "./MetaAdsPeriodSelector";
import { ReachFrequencySection } from "./ReachFrequencySection";

import type { ChannelMetric, MetaAdsPeriod, MetaAdsDashboardTab } from "../../../../types/metrics";

interface MetaAdsOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  onExpandToTab?: (tab: MetaAdsDashboardTab) => void;
  initialTab?: string | null;
}

/**
 *
 */
export function MetaAdsOverviewPanel({
  channel,
  onClose,
  onExpand,
  onExpandToTab,
}: MetaAdsOverviewPanelProps) {
  const [period, setPeriod] = useState<MetaAdsPeriod>("30d");
  const { data, isLoading } = useChannelDashboard(channel.slug, period);
  const { data: campaignData } = useCampaignPerformance(period);
  const { currency: tenantCurrency } = useTenantLocale();

  return (
    <div className="flex h-full flex-col">
      <DetailPanelHeader className="flex-row items-center justify-between">
        <DetailPanelTitle>{channel.name}</DetailPanelTitle>
        <DetailPanelClose onClose={onClose} />
      </DetailPanelHeader>

      <div className="flex items-center justify-between px-4 py-2 border-b">
        <MetaAdsPeriodSelector value={period} onChange={setPeriod} />
        {onExpand && (
          <Button variant="ghost" size="sm" onClick={onExpand} className="gap-1.5 text-xs">
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

            {/* Top Campaigns Preview */}
            {campaignData && campaignData.campaigns.length > 0 && (
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-widest mb-2">
                  Top campañas por ROAS
                </p>
                <div className="rounded-lg border bg-card p-3 space-y-1">
                  {[...campaignData.campaigns]
                    .filter((c) => c.metrics.roas != null && c.metrics.roas > 0)
                    .sort((a, b) => (b.metrics.roas ?? 0) - (a.metrics.roas ?? 0))
                    .slice(0, 3)
                    .map((camp) => (
                      <div
                        key={camp.externalId}
                        className="flex items-center justify-between py-1.5 border-b border-border/50 last:border-0"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "w-1.5 h-1.5 rounded-full",
                              camp.effectiveStatus === "ACTIVE"
                                ? "bg-emerald-500"
                                : camp.health === "critical"
                                  ? "bg-red-500"
                                  : camp.effectiveStatus === "PAUSED"
                                    ? "bg-zinc-500"
                                    : "bg-amber-500",
                            )}
                          />
                          <span className="text-xs truncate max-w-[180px]">{camp.name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[11px] text-muted-foreground tabular-nums">
                            {formatMoney(
                              camp.metrics.spend,
                              campaignData.currency || tenantCurrency,
                            )}
                          </span>
                          <span
                            className={cn(
                              "text-xs font-semibold tabular-nums",
                              (camp.metrics.roas ?? 0) >= 2
                                ? "text-emerald-500"
                                : (camp.metrics.roas ?? 0) >= 1
                                  ? "text-amber-500"
                                  : "text-red-500",
                            )}
                          >
                            {camp.metrics.roas?.toFixed(1)}x
                          </span>
                        </div>
                      </div>
                    ))}
                  <button
                    onClick={() => onExpandToTab?.("campanas")}
                    className="text-[11px] text-blue-400 mt-2 hover:underline"
                  >
                    Ver todas las campañas →
                  </button>
                </div>
              </div>
            )}

            <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />
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
