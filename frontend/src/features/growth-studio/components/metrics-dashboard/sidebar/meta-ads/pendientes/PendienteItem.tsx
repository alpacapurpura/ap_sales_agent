"use client";

import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format-money";
import type { CampaignWithMetrics } from "../../../../../types/metrics";

export type PendingReason = "no_offer" | "no_utm";

interface PendienteItemProps {
  campaign: CampaignWithMetrics;
  reason: PendingReason;
  currency: string;
  isSelected: boolean;
  onClick: () => void;
}

const REASON_LABEL: Record<PendingReason, string> = {
  no_offer: "Sin offer",
  no_utm: "Sin UTM",
};

const REASON_COLORS: Record<PendingReason, string> = {
  no_offer: "bg-amber-500/10 text-amber-400",
  no_utm: "bg-blue-500/10 text-blue-400",
};

function statusDotColor(status: string | null): string {
  const s = (status ?? "").toUpperCase();
  if (s === "ACTIVE") return "bg-emerald-500";
  if (s === "PAUSED" || s === "CAMPAIGN_PAUSED") return "bg-zinc-500";
  return "bg-zinc-500";
}

export function PendienteItem({
  campaign,
  reason,
  currency,
  isSelected,
  onClick,
}: PendienteItemProps) {
  const isPaused =
    (campaign.effectiveStatus ?? "").toUpperCase() === "PAUSED" ||
    (campaign.effectiveStatus ?? "").toUpperCase() === "CAMPAIGN_PAUSED";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "w-full text-left px-4 py-3 border-b border-zinc-800/40 transition-colors",
        isSelected
          ? "bg-blue-500/10 border-l-2 border-l-blue-500"
          : "hover:bg-zinc-800/20 border-l-2 border-l-transparent",
        isPaused && "opacity-60",
      )}
    >
      <div className="flex items-center gap-2">
        <span
          className={cn(
            "inline-block h-2 w-2 rounded-full shrink-0",
            statusDotColor(campaign.effectiveStatus),
          )}
        />
        <span className="text-sm font-medium truncate">{campaign.name}</span>
      </div>
      <div className="flex items-center gap-2 mt-1 ml-4">
        <span className="text-[10px] text-zinc-500">
          {isPaused ? "Pausada · " : ""}
          {formatMoney(campaign.metrics.spend, currency)}
          {campaign.metrics.roas != null && ` · ROAS ${campaign.metrics.roas.toFixed(1)}x`}
        </span>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-1.5 py-0.5 text-[9px] font-medium",
            REASON_COLORS[reason],
          )}
        >
          {REASON_LABEL[reason]}
        </span>
      </div>
    </button>
  );
}
