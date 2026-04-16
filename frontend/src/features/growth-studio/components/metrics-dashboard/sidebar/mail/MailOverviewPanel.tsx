"use client";

import { ExternalLink, Loader2, Mail, RefreshCw, AlertTriangle } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DetailPanelHeader,
  DetailPanelTitle,
  DetailPanelClose,
} from "@/components/ui/detail-panel";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatTenantDateTime } from "@/lib/format-date";
import { cn } from "@/lib/utils";

import { useMailDashboard } from "../../../../hooks/use-mail-dashboard";
import { useSyncChannel } from "../../../../hooks/use-sync-channel";
import { HeroKpiGrid } from "../shared/HeroKpiGrid";
import { PeriodSelector } from "../shared/PeriodSelector";

import { MailCampaignCards } from "./MailCampaignCards";
import { MailDeliverabilityHealth } from "./MailDeliverabilityHealth";
import { MailHealthScore } from "./MailHealthScore";

import type { FunnelStep, ChannelMetric, MetaAdsPeriod } from "../../../../types/metrics";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const HERO_METRICS = [
  "open_rate",
  "click_to_open_rate",
  "deliverability_rate",
  "list_growth_rate",
] as const;

// ---------------------------------------------------------------------------
// Mini Funnel (inline helper — Enviados -> Abiertos -> Clicks)
// ---------------------------------------------------------------------------

interface MailMiniFunnelProps {
  steps: FunnelStep[];
}

function MailMiniFunnel({ steps }: MailMiniFunnelProps) {
  if (steps.length === 0) return null;
  const maxValue = Math.max(...steps.map((s) => s.value), 1);

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Funnel de Email
      </h4>
      <div className="space-y-1.5">
        {steps.map((step, i) => (
          <div key={step.metricName} className="space-y-0.5">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{step.label}</span>
              <div className="flex items-center gap-2">
                <span className="font-medium tabular-nums">
                  {step.value.toLocaleString("es-ES")}
                </span>
                {step.conversionRate != null && i > 0 && (
                  <span className="text-muted-foreground">({step.conversionRate.toFixed(1)}%)</span>
                )}
              </div>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all",
                  i === 0 ? "bg-amber-500" : i === 1 ? "bg-amber-400" : "bg-amber-300",
                )}
                // Inline style required for dynamic percentage width calculation
                style={{ width: `${Math.max((step.value / maxValue) * 100, 2)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// MailOverviewPanel
// ---------------------------------------------------------------------------

interface MailOverviewPanelProps {
  channel: ChannelMetric;
  onClose: () => void;
  onExpand?: () => void;
  initialTab?: string | null;
}

export function MailOverviewPanel({ channel, onClose, onExpand }: MailOverviewPanelProps) {
  const { timezone } = useTenantLocale();
  const [period, setPeriod] = useState<MetaAdsPeriod>("30d");
  const { data, isLoading, isError, error } = useMailDashboard(period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel(channel.slug ?? "email-nurture");

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <DetailPanelHeader className="flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Mail className="h-5 w-5 text-amber-500" />
          <DetailPanelTitle>{channel.name}</DetailPanelTitle>
        </div>
        <DetailPanelClose onClose={onClose} />
      </DetailPanelHeader>

      {/* Toolbar: Period + Sync + Dashboard button */}
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
              aria-label="Ver dashboard completo"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              Ver Dashboard Completo
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
            <AlertTriangle className="h-8 w-8 text-amber-500" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">
                No se pudo cargar el dashboard de email
              </p>
              <p className="text-xs text-muted-foreground max-w-[280px]">
                {error instanceof Error
                  ? error.message
                  : "Verifica que el endpoint de email esté disponible e intenta de nuevo."}
              </p>
            </div>
          </div>
        ) : data ? (
          <>
            {/* Health Score */}
            <MailHealthScore healthScore={data.healthScore} />

            {/* Hero KPI Grid */}
            <HeroKpiGrid
              kpis={data.kpis}
              timeSeries={data.timeSeries}
              heroMetrics={HERO_METRICS}
              gradientPrefix="mail"
              showMetricInfoCard
              formatOptions={{ percentDecimals: 1 }}
            />

            {/* Mini Funnel: Enviados -> Abiertos -> Clicks */}
            <MailMiniFunnel steps={data.funnel} />

            {/* Best + Worst Campaigns */}
            <MailCampaignCards
              bestCampaign={data.bestCampaign}
              worstCampaign={data.worstCampaign}
            />

            {/* Deliverability Health (existing component) */}
            <MailDeliverabilityHealth kpis={data.kpis} />
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
