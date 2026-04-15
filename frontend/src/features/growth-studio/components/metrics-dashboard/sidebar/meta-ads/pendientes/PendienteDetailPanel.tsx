"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import { OfferAssignmentDropdown } from "./OfferAssignmentDropdown";

import type { CampaignWithMetrics } from "../../../../../types/metrics";
import type { OfferSummary } from "../../../../../types/offer-association";

interface PendienteDetailPanelProps {
  campaign: CampaignWithMetrics | null;
  currency: string;
  offers: OfferSummary[];
  onAssigned: () => void;
}

function statusLabel(status: string | null): string {
  const s = (status ?? "").toUpperCase();
  if (s === "ACTIVE") return "Activa";
  if (s === "PAUSED" || s === "CAMPAIGN_PAUSED") return "Pausada";
  if (s === "COMPLETED" || s === "ARCHIVED") return "Completada";
  return status ?? "Desconocido";
}

function objectiveLabel(objective: string | null): string {
  if (!objective) return "";
  const map: Record<string, string> = {
    OUTCOME_SALES: "Ventas",
    OUTCOME_LEADS: "Leads",
    OUTCOME_ENGAGEMENT: "Interacción",
    OUTCOME_AWARENESS: "Alcance",
    OUTCOME_TRAFFIC: "Tráfico",
    CONVERSIONS: "Conversiones",
    MESSAGES: "Mensajes",
    LEAD_GENERATION: "Leads",
  };
  return map[objective] ?? objective.replace(/^OUTCOME_/, "").replace(/_/g, " ");
}

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

export function PendienteDetailPanel({
  campaign,
  currency,
  offers,
  onAssigned,
}: PendienteDetailPanelProps) {
  if (!campaign) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
        Selecciona una campaña de la lista
      </div>
    );
  }

  const { metrics } = campaign;
  const statusDot =
    (campaign.effectiveStatus ?? "").toUpperCase() === "ACTIVE" ? "bg-emerald-500" : "bg-zinc-500";

  return (
    <div className="flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-zinc-800">
        <h2 className="text-lg font-semibold">{campaign.name}</h2>
        <div className="flex items-center gap-2 mt-1">
          <span className={cn("inline-block h-2 w-2 rounded-full", statusDot)} />
          <span className="text-xs text-zinc-500">
            {statusLabel(campaign.effectiveStatus)}
            {campaign.objective && ` · ${objectiveLabel(campaign.objective)}`}
            {` · ${campaign.adSetsCount} ad set${campaign.adSetsCount !== 1 ? "s" : ""}`}
            {` · ${campaign.adsCount} anuncio${campaign.adsCount !== 1 ? "s" : ""}`}
          </span>
        </div>
      </div>

      {/* Assignment section */}
      <div className="mx-6 mt-4 rounded-xl border-2 border-amber-500/30 bg-amber-500/5 p-4">
        <OfferAssignmentDropdown
          campaignExternalId={campaign.externalId}
          offers={offers}
          onAssigned={onAssigned}
        />
      </div>

      {/* Metrics grid */}
      <div className="px-6 py-4">
        <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500 mb-3">
          Rendimiento actual
        </p>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">Inversión</p>
              <p className="text-lg font-bold mt-1 tabular-nums">
                {formatMoney(metrics.spend, currency)}
              </p>
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">Resultados</p>
              <p className="text-lg font-bold mt-1 tabular-nums">
                {metrics.conversions.toLocaleString()}
              </p>
              {campaign.objective && (
                <p className="text-[10px] text-zinc-600">
                  {objectiveLabel(campaign.objective).toLowerCase()}
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">CPA</p>
              <p
                className={cn("text-lg font-bold mt-1 tabular-nums", healthColor(campaign.health))}
              >
                {metrics.cpa != null ? formatMoney(metrics.cpa, currency) : "—"}
              </p>
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-3">
              <p className="text-[10px] text-zinc-500">ROAS</p>
              <p
                className={cn("text-lg font-bold mt-1 tabular-nums", healthColor(campaign.health))}
              >
                {metrics.roas != null ? `${metrics.roas.toFixed(1)}x` : "—"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Secondary metrics */}
        <div className="grid grid-cols-4 gap-3 mt-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">CTR</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.ctr != null ? `${metrics.ctr.toFixed(1)}%` : "—"}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">CPC</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.cpc != null ? formatMoney(metrics.cpc, currency) : "—"}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">Impresiones</p>
            <p className="text-sm font-semibold mt-1 tabular-nums">
              {metrics.impressions.toLocaleString()}
            </p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
            <p className="text-[10px] text-zinc-500">Frecuencia</p>
            <p
              className={cn(
                "text-sm font-semibold mt-1 tabular-nums",
                metrics.frequency != null && metrics.frequency > 4
                  ? "text-red-400"
                  : metrics.frequency != null && metrics.frequency > 3
                    ? "text-amber-400"
                    : "",
              )}
            >
              {metrics.frequency != null ? metrics.frequency.toFixed(1) : "—"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
