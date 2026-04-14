"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  ChevronDown,
  Copy,
  Loader2,
  Pause,
  Play,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { formatMoney } from "@/lib/format-money";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatTenantDate, formatTenantDateTime } from "@/lib/format-date";
import { cn } from "@/lib/utils";
import { ChartSection } from "../../shared/ChartSection";
import { useAssociations } from "../../../../../api/offer-association-api";
import { archetypeEmoji } from "../../../../../types/offer-association";
import type {
  CampaignPerformanceData,
  CampaignWithMetrics,
  MetaAdsPeriod,
} from "../../../../../types/metrics";
import type { Association } from "../../../../../types/offer-association";
import { OfferAssignmentDrawerConnected } from "../OfferAssignmentDrawerConnected";
import { OfferReassignPopover } from "../OfferReassignPopover";
import { ImprovementNotesPanel } from "../notices/ImprovementNotesPanel";
import { useIgnoredNotices } from "../notices/useIgnoredNotices";
import type { ImprovementNotice, SeverityBreakdown } from "../notices/types";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CampaignsTabProps {
  data: CampaignPerformanceData | undefined;
  isLoading: boolean;
  currency?: string;
  period?: MetaAdsPeriod;
  /** Notices bucketed for this tab by the dashboard-level useMetaAdsNotices hook. */
  notices?: ImprovementNotice[];
  noticesSeverity?: SeverityBreakdown;
  /** Navigate to Pendientes tab */
  onNavigateToPendientes?: () => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Resolve a currency string falling back to the provided fallback. */
function cur(currency: string | undefined | null, fallback = "USD"): string {
  return currency || fallback;
}

/** Format a monetary value with fallback currency. */
function money(value: number, currency: string | undefined | null, fallback = "USD"): string {
  return formatMoney(value, cur(currency, fallback));
}

/** Map campaign effective status to a visual status category. */
function campaignStatusCategory(
  campaign: CampaignWithMetrics,
): "active" | "learning" | "error" | "paused" | "completed" {
  const es = (campaign.effectiveStatus ?? "").toUpperCase();
  const health = campaign.health;

  if (es === "PAUSED") return "paused";
  if (es === "CAMPAIGN_PAUSED") return "paused";
  if (es === "COMPLETED" || es === "ARCHIVED") return "completed";

  // Learning / in-process
  if (es === "IN_PROCESS" || es === "PENDING_REVIEW" || es === "WITH_ISSUES") {
    if (es === "WITH_ISSUES" || health === "critical") return "error";
    return "learning";
  }

  // Active but with health issues
  if (health === "critical") return "error";
  if (health === "warning") return "learning";

  return "active";
}

/** Sort priority: critical first, then warning, then good/active, then paused/completed. */
function statusSortOrder(campaign: CampaignWithMetrics): number {
  const cat = campaignStatusCategory(campaign);
  const order: Record<string, number> = {
    error: 0,
    learning: 1,
    active: 2,
    paused: 3,
    completed: 4,
  };
  return order[cat] ?? 5;
}

/** Status dot CSS classes. */
function statusDotClasses(category: ReturnType<typeof campaignStatusCategory>): string {
  const base = "inline-block h-2 w-2 shrink-0 rounded-full";
  switch (category) {
    case "active":
      return cn(base, "bg-emerald-500 shadow-[0_0_0_0_rgba(34,197,94,0.4)] animate-pulse");
    case "learning":
      return cn(base, "bg-amber-500 shadow-[0_0_0_0_rgba(234,179,8,0.4)] animate-pulse");
    case "error":
      return cn(base, "bg-red-500 shadow-[0_0_0_0_rgba(239,68,68,0.4)] animate-pulse");
    case "paused":
    case "completed":
      return cn(base, "bg-zinc-500");
  }
}

/** CTR indicator dot color. */
function ctrIndicator(ctr: number | null): string {
  if (ctr == null) return "bg-zinc-500";
  if (ctr >= 2) return "bg-emerald-500";
  if (ctr >= 1) return "bg-amber-500";
  return "bg-red-500";
}

/** Frequency indicator dot color. */
function freqIndicator(freq: number | null): string {
  if (freq == null) return "bg-zinc-500";
  if (freq < 3) return "bg-emerald-500";
  if (freq <= 4) return "bg-amber-500";
  return "bg-red-500";
}

/** Color class for a metric based on campaign health. */
function healthColor(health: "good" | "warning" | "critical"): string {
  switch (health) {
    case "good":
      return "text-emerald-400";
    case "warning":
      return "text-amber-400";
    case "critical":
      return "text-red-400";
  }
}

/** Health badge label. */
function healthBadgeLabel(health: "good" | "warning" | "critical"): string | null {
  switch (health) {
    case "good":
      return "Excelente";
    case "warning":
      return "Aceptable";
    case "critical":
      return "Atención";
  }
}

/** Health badge CSS. */
function healthBadgeClasses(health: "good" | "warning" | "critical"): string {
  switch (health) {
    case "good":
      return "bg-emerald-500/10 text-emerald-400";
    case "warning":
      return "bg-amber-500/10 text-amber-400";
    case "critical":
      return "bg-red-500/10 text-red-400";
  }
}

/** Budget pacing bar color based on ratio. */
function budgetBarColor(ratio: number): string {
  if (ratio > 0.9) return "bg-red-500/60";
  if (ratio > 0.7) return "bg-amber-500/60";
  return "bg-emerald-500/60";
}

/** Formatted objective label. */
function objectiveLabel(objective: string | null): string {
  if (!objective) return "";
  const map: Record<string, string> = {
    OUTCOME_SALES: "Ventas",
    OUTCOME_LEADS: "Leads",
    OUTCOME_ENGAGEMENT: "Interacción",
    OUTCOME_AWARENESS: "Alcance",
    OUTCOME_TRAFFIC: "Tráfico",
    OUTCOME_APP_PROMOTION: "App",
    CONVERSIONS: "Conversiones",
    LINK_CLICKS: "Clics",
    REACH: "Alcance",
    BRAND_AWARENESS: "Marca",
    POST_ENGAGEMENT: "Interacción",
    VIDEO_VIEWS: "Video",
    LEAD_GENERATION: "Leads",
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, "").replace(/_/g, " ");
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Header tooltip wrapper for table column headers. */
function HeaderTooltip({ children, content }: { children: React.ReactNode; content: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="cursor-help">{children}</span>
      </TooltipTrigger>
      <TooltipContent side="top" className="max-w-[260px] text-xs">
        {content}
      </TooltipContent>
    </Tooltip>
  );
}

/** A small inline tooltip icon for campaign-row badges. */
function BadgeTooltip({ children, content }: { children: React.ReactNode; content: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipContent side="top" className="max-w-[260px] text-xs">
        {content}
      </TooltipContent>
    </Tooltip>
  );
}

// ---------------------------------------------------------------------------
// Section 1: Summary KPIs
// ---------------------------------------------------------------------------

function CampaignSummaryKpis({
  data,
  currency,
}: {
  data: CampaignPerformanceData;
  currency: string;
}) {
  const { campaigns } = data;

  const activeCount = campaigns.filter(
    (c) => campaignStatusCategory(c) === "active" || campaignStatusCategory(c) === "learning",
  ).length;
  const pausedCount = campaigns.filter((c) => campaignStatusCategory(c) === "paused").length;
  const errorCount = campaigns.filter((c) => campaignStatusCategory(c) === "error").length;

  const totalSpend = campaigns.reduce((sum, c) => sum + c.metrics.spend, 0);
  const totalConversions = campaigns.reduce((sum, c) => sum + c.metrics.conversions, 0);

  // Weighted average ROAS (by spend)
  const totalSpendForRoas = campaigns.reduce(
    (sum, c) => sum + (c.metrics.roas != null ? c.metrics.spend : 0),
    0,
  );
  const weightedRoas =
    totalSpendForRoas > 0
      ? campaigns.reduce((sum, c) => sum + (c.metrics.roas ?? 0) * c.metrics.spend, 0) /
        totalSpendForRoas
      : 0;

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {/* Active / Total */}
      <div className="space-y-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p
          className="text-[11px] uppercase tracking-wider text-zinc-500"
          title="Campañas que están entregando anuncios ahora mismo vs el total de campañas en tu cuenta"
        >
          Activas / Total
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tabular-nums">{activeCount}</span>
          <span className="text-sm text-zinc-500">/ {campaigns.length}</span>
        </div>
        <div className="mt-1 flex flex-wrap gap-1.5">
          {activeCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
              {activeCount} activa{activeCount !== 1 ? "s" : ""}
            </span>
          )}
          {pausedCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-zinc-500/10 px-2 py-0.5 text-[10px] font-medium text-zinc-400">
              {pausedCount} pausada{pausedCount !== 1 ? "s" : ""}
            </span>
          )}
          {errorCount > 0 && (
            <span className="inline-flex items-center rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400">
              {errorCount} error{errorCount !== 1 ? "es" : ""}
            </span>
          )}
        </div>
      </div>

      {/* Total Spend */}
      <div className="space-y-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p
          className="text-[11px] uppercase tracking-wider text-zinc-500"
          title="Total gastado en todas las campañas durante el periodo seleccionado. Incluye todos los tipos de campaña."
        >
          Inversión Total
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tabular-nums">{money(totalSpend, currency)}</span>
        </div>
      </div>

      {/* Total Results */}
      <div className="space-y-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p
          className="text-[11px] uppercase tracking-wider text-zinc-500"
          title="Total de conversiones (ventas, leads, o el objetivo que configuraste) de todas las campañas combinadas."
        >
          Resultados Totales
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tabular-nums">
            {totalConversions.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Average ROAS */}
      <div className="space-y-1 rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
        <p
          className="text-[11px] uppercase tracking-wider text-zinc-500"
          title="ROAS = Return On Ad Spend. Por cada $1 que inviertes, cuánto recuperas en ventas. Ej: 3.2x significa que por cada $1 ganas $3.20. Arriba de 2x es bueno para la mayoría de negocios."
        >
          ROAS Promedio
        </p>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold tabular-nums">{weightedRoas.toFixed(1)}x</span>
          {weightedRoas >= 2 && (
            <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
              Por encima del promedio
            </span>
          )}
          {weightedRoas > 0 && weightedRoas < 2 && (
            <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
              Por debajo del promedio
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 3: Campaign Row
// ---------------------------------------------------------------------------

function CampaignRow({
  campaign,
  currency,
  association,
  onAssignClick,
}: {
  campaign: CampaignWithMetrics;
  currency: string;
  association: Association | null;
  onAssignClick: () => void;
}) {
  const { timezone } = useTenantLocale();
  const cat = campaignStatusCategory(campaign);
  const isPaused = cat === "paused";
  const isCompleted = cat === "completed";
  const isInactive = isPaused || isCompleted;
  const isLearning = cat === "learning";
  const isError = cat === "error";

  const { metrics } = campaign;

  // Budget pacing
  const dailyBudget = campaign.dailyBudget;
  const budgetRatio =
    dailyBudget && dailyBudget > 0 ? Math.min(metrics.spend / dailyBudget, 1) : null;

  return (
    <div
      id={`campaign-row-${campaign.externalId}`}
      className={cn(
        "scroll-mt-24 border-b border-zinc-800/60 transition-colors hover:bg-zinc-800/30",
        isError && "bg-red-500/[0.02]",
        isInactive && "opacity-60",
      )}
    >
      <div className="grid grid-cols-[1fr_100px_100px_100px_80px_80px_80px_72px_90px] items-center gap-2 px-4 py-3">
        {/* Campaign info */}
        <div className="flex min-w-0 flex-col">
          <div className="flex items-center gap-2">
            <span className={statusDotClasses(cat)} />
            <span className={cn("truncate text-sm font-medium", isInactive && "text-zinc-400")}>
              {campaign.name}
            </span>
            {isLearning && (
              <BadgeTooltip content="Meta está optimizando esta campaña. Evita hacer cambios grandes durante esta fase.">
                <span className="inline-flex shrink-0 items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
                  Aprendiendo
                </span>
              </BadgeTooltip>
            )}
            {isError && (
              <BadgeTooltip content="Esta campaña tiene un problema de rendimiento: el costo por resultado es muy alto comparado con tu promedio.">
                <span className="inline-flex shrink-0 items-center rounded-full bg-red-500/10 px-2 py-0.5 text-[10px] font-medium text-red-400">
                  Necesita atención
                </span>
              </BadgeTooltip>
            )}
            {isPaused && (
              <span className="inline-flex shrink-0 items-center rounded-full bg-zinc-500/10 px-2 py-0.5 text-[10px] font-medium text-zinc-500">
                Pausada
              </span>
            )}
            {isCompleted && (
              <span className="inline-flex shrink-0 items-center rounded-full bg-zinc-500/10 px-2 py-0.5 text-[10px] font-medium text-zinc-600">
                Completada
              </span>
            )}
          </div>
          <div className="mt-0.5 flex flex-wrap items-center gap-2">
            {campaign.objective && (
              <span className="inline-flex items-center rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">
                {objectiveLabel(campaign.objective)}
              </span>
            )}
            {/* Offer association badge */}
            {association ? (
              <OfferReassignPopover
                campaign={{ externalId: campaign.externalId, name: campaign.name }}
                association={association}
              >
                {association.associationType === "excluded_branding" ? (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-full border border-zinc-600/60 bg-zinc-700/10 px-2 py-0.5 text-[10px] text-zinc-400 transition-colors hover:border-zinc-500 hover:bg-zinc-700/20 hover:text-zinc-300"
                  >
                    <span aria-hidden="true">🎯</span>
                    Branding
                  </button>
                ) : (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-full border border-blue-500/40 bg-blue-500/10 px-2 py-0.5 text-[10px] text-blue-400 transition-colors hover:border-blue-400 hover:bg-blue-500/20 hover:text-blue-300"
                  >
                    <span aria-hidden="true">{archetypeEmoji(association.offerArchetype)}</span>
                    {association.offerName ?? "Offer asociada"}
                  </button>
                )}
              </OfferReassignPopover>
            ) : (
              <BadgeTooltip content="Click para asignar esta campaña a una offer del Offer Ladder.">
                <button
                  type="button"
                  onClick={onAssignClick}
                  className="inline-flex items-center gap-1 rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400 transition-colors hover:border-amber-400 hover:bg-amber-500/20 hover:text-amber-300"
                >
                  Sin offer asignada
                  <span aria-hidden="true">→</span>
                </button>
              </BadgeTooltip>
            )}
            <span className="text-[10px] text-zinc-600">
              {campaign.adSetsCount} ad set{campaign.adSetsCount !== 1 ? "s" : ""} &middot;{" "}
              {campaign.adsCount} anuncio{campaign.adsCount !== 1 ? "s" : ""}
            </span>
            {/* Budget pacing bar */}
            {budgetRatio != null && dailyBudget != null && !isInactive && (
              <div className="flex items-center gap-1.5">
                <div className="h-1 w-16 overflow-hidden rounded-sm bg-zinc-700">
                  <div
                    className={cn("h-full rounded-sm", budgetBarColor(budgetRatio))}
                    style={{ width: `${(budgetRatio * 100).toFixed(0)}%` }}
                  />
                </div>
                <span className="text-[10px] text-zinc-500">
                  {money(metrics.spend, currency)} / {money(dailyBudget, currency)} diario
                </span>
              </div>
            )}
            {/* Paused date */}
            {isPaused && campaign.stopTime && (
              <span className="text-[10px] text-zinc-600">
                Pausada el {formatTenantDate(campaign.stopTime, timezone, "d MMM")}
              </span>
            )}
          </div>
        </div>

        {/* Spend */}
        <div className="text-right">
          <p className={cn("text-sm tabular-nums", isInactive ? "text-zinc-500" : "font-semibold")}>
            {money(metrics.spend, currency)}
          </p>
          {!isInactive && metrics.spend > 0 && <p className="text-[10px] text-zinc-500">total</p>}
        </div>

        {/* Results */}
        <div className="text-right">
          <p className={cn("text-sm tabular-nums", isInactive ? "text-zinc-500" : "font-semibold")}>
            {metrics.conversions.toLocaleString()}
          </p>
          {!isInactive && campaign.objective && (
            <p className="text-[10px] text-zinc-500">
              {objectiveLabel(campaign.objective).toLowerCase()}
            </p>
          )}
        </div>

        {/* CPA */}
        <div className="text-right">
          <p
            className={cn(
              "text-sm tabular-nums",
              isInactive ? "text-zinc-500" : cn("font-semibold", healthColor(campaign.health)),
            )}
          >
            {metrics.cpa != null ? money(metrics.cpa, currency) : "—"}
          </p>
          {!isInactive && metrics.cpa != null && (
            <span
              className={cn(
                "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px]",
                healthBadgeClasses(campaign.health),
              )}
            >
              {healthBadgeLabel(campaign.health)}
            </span>
          )}
        </div>

        {/* ROAS */}
        <div className="text-right">
          <p
            className={cn(
              "text-sm tabular-nums",
              isInactive ? "text-zinc-500" : cn("font-bold", healthColor(campaign.health)),
            )}
          >
            {metrics.roas != null ? `${metrics.roas.toFixed(1)}x` : "—"}
          </p>
        </div>

        {/* CTR */}
        <div className="text-right">
          <p className={cn("text-sm tabular-nums", isInactive && "text-zinc-500")}>
            {metrics.ctr != null ? `${metrics.ctr.toFixed(1)}%` : "—"}
          </p>
          {!isInactive && metrics.ctr != null && (
            <span
              className={cn(
                "mt-0.5 inline-block h-1.5 w-1.5 rounded-full",
                ctrIndicator(metrics.ctr),
              )}
            />
          )}
        </div>

        {/* CPC */}
        <div className="text-right">
          <p className={cn("text-sm tabular-nums", isInactive && "text-zinc-500")}>
            {metrics.cpc != null ? money(metrics.cpc, currency) : "—"}
          </p>
        </div>

        {/* Frequency */}
        <div className="text-right">
          <p
            className={cn(
              "text-sm tabular-nums",
              isInactive
                ? "text-zinc-500"
                : metrics.frequency != null && metrics.frequency > 4
                  ? "text-red-400"
                  : metrics.frequency != null && metrics.frequency > 3
                    ? "text-amber-400"
                    : "",
            )}
          >
            {metrics.frequency != null ? metrics.frequency.toFixed(1) : "—"}
          </p>
          {!isInactive && metrics.frequency != null && (
            <span
              className={cn(
                "mt-0.5 inline-block h-1.5 w-1.5 rounded-full",
                freqIndicator(metrics.frequency),
              )}
            />
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-1">
          {!isInactive && (
            <>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="rounded-md border border-zinc-700 bg-zinc-800 p-1.5 text-zinc-400 transition-all hover:-translate-y-px hover:border-emerald-500/30 hover:text-emerald-400"
                  >
                    <TrendingUp className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  Aumentar budget +20%
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className={cn(
                      "rounded-md border p-1.5 transition-all hover:-translate-y-px",
                      isError
                        ? "border-red-500/30 bg-red-500/10 text-red-400 hover:bg-red-500/20"
                        : "border-zinc-700 bg-zinc-800 text-zinc-400 hover:border-amber-500/30 hover:text-amber-400",
                    )}
                  >
                    <Pause className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  Pausar campaña{isError ? " (recomendado)" : ""}
                </TooltipContent>
              </Tooltip>
            </>
          )}
          {isPaused && (
            <>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="rounded-md border border-zinc-700 bg-zinc-800 p-1.5 text-zinc-500 transition-all hover:-translate-y-px hover:text-emerald-400"
                  >
                    <Play className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  Reactivar campaña
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    className="rounded-md border border-zinc-700 bg-zinc-800 p-1.5 text-zinc-500 transition-all hover:-translate-y-px hover:text-blue-400"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  Duplicar campaña
                </TooltipContent>
              </Tooltip>
            </>
          )}
          {isCompleted && (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  className="rounded-md border border-zinc-700 bg-zinc-800 p-1.5 text-zinc-500 transition-all hover:-translate-y-px hover:text-blue-400"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                Duplicar campaña con nuevos parámetros
              </TooltipContent>
            </Tooltip>
          )}
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                className={cn(
                  "rounded-md border border-zinc-700 bg-zinc-800 p-1.5 transition-all hover:-translate-y-px hover:text-blue-400",
                  isInactive ? "text-zinc-500" : "text-zinc-400",
                )}
              >
                <ChevronDown className="h-3.5 w-3.5" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="top" className="text-xs">
              Ver detalles
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section 4: Indicator Guide
// ---------------------------------------------------------------------------

function IndicatorGuide() {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/30 p-4">
      <p className="mb-3 text-xs font-medium text-zinc-400">Guía de indicadores</p>
      <div className="grid grid-cols-2 gap-4 text-[11px] lg:grid-cols-4">
        {/* Status */}
        <div className="space-y-2">
          <p className="font-medium text-zinc-300">Estado</p>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-zinc-400">Activa — entregando</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              <span className="text-zinc-400">Aprendiendo — no tocar</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-red-500" />
              <span className="text-zinc-400">Problema — revisar</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-zinc-500" />
              <span className="text-zinc-400">Pausada / Completada</span>
            </div>
          </div>
        </div>

        {/* Performance */}
        <div className="space-y-2">
          <p className="font-medium text-zinc-300">Rendimiento</p>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-emerald-400">
                Excelente
              </span>
              <span className="text-zinc-500">Mejor que promedio</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-amber-400">
                Aceptable
              </span>
              <span className="text-zinc-500">Dentro de rango</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-red-500/10 px-2 py-0.5 text-red-400">Atención</span>
              <span className="text-zinc-500">Alerta</span>
            </div>
          </div>
        </div>

        {/* Columns */}
        <div className="space-y-2">
          <p className="font-medium text-zinc-300">Columnas</p>
          <div className="space-y-1 text-zinc-400">
            <p>
              <strong className="text-zinc-300">CPA</strong> — Costo por resultado
            </p>
            <p>
              <strong className="text-zinc-300">ROAS</strong> — Retorno por $1 invertido
            </p>
            <p>
              <strong className="text-zinc-300">CTR</strong> — % que hizo clic
            </p>
            <p>
              <strong className="text-zinc-300">CPC</strong> — Costo por clic
            </p>
          </div>
        </div>

        {/* Frequency */}
        <div className="space-y-2">
          <p className="font-medium text-zinc-300">Frequency</p>
          <div className="space-y-1 text-zinc-400">
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              {"< 3 — Saludable"}
            </div>
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
              {"3-4 — Atención"}
            </div>
            <div className="flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
              {"> 4 — Saturación"}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

const EMPTY_SEVERITY: SeverityBreakdown = { critical: 0, warning: 0, info: 0 };

export function CampaignsTab({
  data,
  isLoading,
  currency,
  period = "30d",
  notices = [],
  noticesSeverity = EMPTY_SEVERITY,
  onNavigateToPendientes,
}: CampaignsTabProps) {
  const { timezone, currency: tenantCurrency } = useTenantLocale();
  const searchParams = useSearchParams();
  const { ignore } = useIgnoredNotices();

  // The Resumen overview can deep-link to this tab and request that the
  // notices panel starts expanded. Read it once on mount; subsequent tab
  // visits (regular click) do not force the panel open.
  const forceOpenNotices = searchParams?.get("notices") === "open";

  // Offer-association layer — associations are used for row-level badges.
  // Campaign list + offer list are fetched internally by the connected drawer,
  // so this component only needs the association map for the badges.
  const { data: associations } = useAssociations();

  // Drawer state + auto-open from ?assign=true query param
  const shouldAutoOpen = searchParams?.get("assign") === "true";
  const [isDrawerOpen, setIsDrawerOpen] = useState(shouldAutoOpen);

  // Index associations by target for O(1) lookup from rows
  const associationByCampaign = useMemo(() => {
    const map = new Map<string, Association>();
    for (const a of associations ?? []) {
      if (a.targetType === "campaign") {
        map.set(a.targetExternalId, a);
      }
    }
    return map;
  }, [associations]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // No data state
  if (!data || data.campaigns.length === 0) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        <p className="font-medium">Campañas</p>
        <p className="mt-1">
          No hay campañas disponibles. Conecta tu cuenta de Meta Ads para ver el rendimiento.
        </p>
      </div>
    );
  }

  const resolvedCurrency = cur(currency ?? data.currency, tenantCurrency);

  // Sort campaigns: critical first, then warning, then good, then paused/completed
  const sortedCampaigns = [...data.campaigns].sort(
    (a, b) => statusSortOrder(a) - statusSortOrder(b),
  );

  const unassignedActiveCount = sortedCampaigns.filter((c) => {
    const isActive = (c.effectiveStatus ?? "").toUpperCase() === "ACTIVE";
    return isActive && !associationByCampaign.has(c.externalId);
  }).length;

  return (
    <TooltipProvider delayDuration={200}>
      <ChartSection slug="campanas-tabla">
        <div className="space-y-6">
          {/* Section 0: Tab header */}
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Campañas</h2>
              <p className="mt-0.5 text-xs text-zinc-500">
                Rendimiento individual por campaña
                {data.lastSynced && (
                  <>
                    {" "}
                    &middot; Última sincronización:{" "}
                    {formatTenantDateTime(data.lastSynced, timezone)}
                  </>
                )}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {unassignedActiveCount > 0 && onNavigateToPendientes && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onNavigateToPendientes}
                  className="gap-1.5 text-amber-400 border-amber-500/30 hover:bg-amber-500/10"
                >
                  {unassignedActiveCount} pendientes →
                </Button>
              )}
              <Button
                type="button"
                variant={unassignedActiveCount > 0 ? "default" : "outline"}
                size="sm"
                onClick={() => setIsDrawerOpen(true)}
                className="gap-1.5"
              >
                <Sparkles className="h-3.5 w-3.5" />
                Asociar offers
              </Button>
            </div>
          </div>

          {/* Section 1: Summary KPIs */}
          <CampaignSummaryKpis data={data} currency={resolvedCurrency} />

          {/* Section 2: Improvement notices (only for ACTIVE campaigns,
              categorized to this tab by the dashboard-level notices hook).
              Collapsed by default; force-open if user navigated from Resumen. */}
          <ImprovementNotesPanel
            notices={notices}
            severity={noticesSeverity}
            forceOpen={forceOpenNotices}
            onIgnore={ignore}
            onNoticeClick={(notice) => {
              if (notice.targetExternalId && typeof window !== "undefined") {
                const el = document.getElementById(`campaign-row-${notice.targetExternalId}`);
                el?.scrollIntoView({ behavior: "smooth", block: "center" });
              }
            }}
          />

          {/* Section 3: Campaign Table */}
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/30">
            {/* Table header */}
            <div className="grid grid-cols-[1fr_100px_100px_100px_80px_80px_80px_72px_90px] gap-2 border-b border-zinc-800 px-4 py-2.5 text-[11px] uppercase tracking-wider text-zinc-500">
              <span>Campaña</span>
              <HeaderTooltip content="Total invertido en esta campaña durante el periodo. Incluye todos los ad sets y anuncios.">
                <span className="block text-right">Inversión</span>
              </HeaderTooltip>
              <HeaderTooltip content="Cantidad de conversiones (ventas, leads, registros) que esta campaña generó.">
                <span className="block text-right">Resultados</span>
              </HeaderTooltip>
              <HeaderTooltip content="CPA = Cost Per Action. Cuánto pagaste en promedio por cada resultado. Menor es mejor.">
                <span className="block text-right">CPA</span>
              </HeaderTooltip>
              <HeaderTooltip content="ROAS = Return On Ad Spend. Cuánto ganas por cada $1 invertido. Ej: 4.1x = ganas $4.10 por $1. Más alto es mejor.">
                <span className="block text-right">ROAS</span>
              </HeaderTooltip>
              <HeaderTooltip content="CTR = Click-Through Rate. % de personas que ven tu anuncio y hacen clic. Indica qué tan atractivo es tu anuncio. Más alto es mejor.">
                <span className="block text-right">CTR</span>
              </HeaderTooltip>
              <HeaderTooltip content="CPC = Cost Per Click. Cuánto pagas por cada clic en tu anuncio. Menor es mejor. Depende de la competencia en tu nicho.">
                <span className="block text-right">CPC</span>
              </HeaderTooltip>
              <HeaderTooltip content="Frequency = cuántas veces en promedio cada persona vio tu anuncio. Arriba de 3 puede causar fatiga (la gente lo ignora).">
                <span className="block text-right">Freq.</span>
              </HeaderTooltip>
              <span className="text-right">Acciones</span>
            </div>

            {/* Campaign rows */}
            {sortedCampaigns.map((campaign) => (
              <CampaignRow
                key={campaign.externalId}
                campaign={campaign}
                currency={resolvedCurrency}
                association={associationByCampaign.get(campaign.externalId) ?? null}
                onAssignClick={() => setIsDrawerOpen(true)}
              />
            ))}
          </div>

          {/* Section 4: Indicator Guide */}
          <IndicatorGuide />
        </div>
      </ChartSection>

      {/* Offer assignment drawer (self-fetching) */}
      <OfferAssignmentDrawerConnected
        open={isDrawerOpen}
        onOpenChange={setIsDrawerOpen}
        period={period}
      />
    </TooltipProvider>
  );
}
