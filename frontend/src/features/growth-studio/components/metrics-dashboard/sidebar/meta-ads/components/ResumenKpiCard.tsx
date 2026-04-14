"use client";

import { HelpCircle, Info, TrendingDown, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { formatMoney } from "@/lib/format-money";
import { cn } from "@/lib/utils";

import { RESUMEN_TOOLTIPS } from "../copy/tooltips";
import type { ResumenKpiCard as ResumenKpiCardData } from "../hooks/useResumenViewData";

interface ResumenKpiCardProps {
  card: ResumenKpiCardData;
  onCtaClick: () => void;
}

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function formatCardValue(card: ResumenKpiCardData): string {
  if (card.kind === "unavailable" || card.value == null) return "—";
  const { value, unit, currency } = card;
  if (unit === "currency") return formatMoney(value, currency);
  if (unit === "percentage") return `${value.toFixed(2)}%`;
  if (unit === "ratio") return `${value.toFixed(2)}x`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString("es");
}

function ariaValueFor(card: ResumenKpiCardData): string {
  if (card.kind === "unavailable" || card.value == null) return "no disponible";
  switch (card.unit) {
    case "currency":
      return `${card.value} ${card.currency}`;
    case "percentage":
      return `${card.value} por ciento`;
    case "ratio":
      return `${card.value} veces`;
    default:
      return card.value.toLocaleString("es");
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ResumenKpiCard({ card, onCtaClick }: ResumenKpiCardProps) {
  // ── CTA variant ─────────────────────────────────────────────────────────
  if (card.kind === "cta") {
    return (
      <div
        role="group"
        aria-label="Acción requerida: asignar campañas"
        className="rounded-lg border border-amber-500/30 bg-amber-500/10 dark:bg-amber-950/30 p-3 space-y-1 flex flex-col justify-between min-h-[92px]"
      >
        <p className="text-[10px] font-semibold text-amber-500 dark:text-amber-400 uppercase tracking-wider">
          Acción requerida
        </p>
        <p className="text-[11px] text-amber-600 dark:text-amber-300/80 leading-snug">
          Asigná cada campaña a un offer para ver métricas por producto
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={onCtaClick}
          className="h-7 border-amber-500/50 text-amber-500 dark:text-amber-400 hover:bg-amber-500/20 hover:text-amber-600 dark:hover:text-amber-300 text-[11px] self-start"
        >
          Asignar ahora
        </Button>
      </div>
    );
  }

  // ── Value / Unavailable variants ────────────────────────────────────────
  const tooltip = RESUMEN_TOOLTIPS[card.tooltipKey];
  const unavailableTooltip = card.unavailableTooltipKey
    ? RESUMEN_TOOLTIPS[card.unavailableTooltipKey]
    : null;

  const isUnavailable = card.kind === "unavailable";
  const deltaPct = card.deltaPct;
  const showDelta = !isUnavailable && deltaPct != null;

  // Delta color semantics (UI-SPEC §7):
  //   higherIsBetter = true  → positive delta is good (emerald), negative bad (red)
  //   higherIsBetter = false → positive delta is bad  (red),     negative good (emerald)
  //   higherIsBetter = null  → neutral muted color regardless of sign
  const deltaToneClass = ((): string => {
    if (!showDelta || deltaPct == null) return "text-muted-foreground";
    if (card.higherIsBetter == null) return "text-muted-foreground";
    const isGood = card.higherIsBetter ? deltaPct >= 0 : deltaPct <= 0;
    return isGood ? "text-emerald-600 dark:text-emerald-500" : "text-red-600 dark:text-red-500";
  })();

  // Aria-label — always includes label, spoken value, delta sentence (when
  // present), and the tooltip body so screen-reader users get the same
  // context a hover user gets.
  const ariaTooltipText = [
    tooltip ? `${tooltip.title}. ${tooltip.body}` : "",
    unavailableTooltip ? `${unavailableTooltip.title}. ${unavailableTooltip.body}` : "",
  ]
    .filter(Boolean)
    .join(" ");

  const ariaLabel = isUnavailable
    ? `${card.label}: dato no disponible.${ariaTooltipText ? ` ${ariaTooltipText}` : ""}`
    : `${card.label}: ${ariaValueFor(card)}${
        showDelta && deltaPct != null ? `, variación ${deltaPct}% respecto al período anterior` : ""
      }.${ariaTooltipText ? ` ${ariaTooltipText}` : ""}`;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          role="group"
          tabIndex={0}
          aria-label={ariaLabel}
          data-testid={`kpi-card-${card.key}`}
          className={cn(
            "rounded-lg border bg-card p-3 space-y-1 relative group min-h-[92px]",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
            isUnavailable && "bg-muted/30",
          )}
        >
          <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <span className="truncate">{card.label}</span>
            <HelpCircle
              className="h-3 w-3 text-muted-foreground/50 opacity-60 group-hover:opacity-100 transition-opacity shrink-0"
              aria-hidden="true"
            />
          </p>

          <div className="flex items-center gap-1.5">
            <p
              className={cn(
                "text-xl font-bold tabular-nums leading-none",
                isUnavailable ? "text-muted-foreground/60" : "text-foreground",
              )}
            >
              {formatCardValue(card)}
            </p>
            {isUnavailable && (
              <Info
                className="h-3 w-3 text-muted-foreground/60 shrink-0"
                aria-hidden="true"
                data-testid="kpi-unavailable-icon"
              />
            )}
          </div>

          {showDelta && deltaPct != null && (
            <span
              className={cn(
                "inline-flex items-center gap-0.5 text-[10px] font-medium",
                deltaToneClass,
              )}
            >
              {deltaPct >= 0 ? (
                <TrendingUp className="h-3 w-3" aria-hidden="true" />
              ) : (
                <TrendingDown className="h-3 w-3" aria-hidden="true" />
              )}
              {Math.abs(deltaPct).toFixed(1)}% vs ant.
            </span>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent side="top" sideOffset={6} className="max-w-xs">
        {tooltip && (
          <div className="space-y-1">
            <p className="font-semibold text-xs">{tooltip.title}</p>
            <p className="text-[11px] text-muted-foreground leading-snug">{tooltip.body}</p>
          </div>
        )}
        {unavailableTooltip && (
          <div className="space-y-1 mt-2 pt-2 border-t">
            <p className="font-semibold text-xs">{unavailableTooltip.title}</p>
            <p className="text-[11px] text-muted-foreground leading-snug">
              {unavailableTooltip.body}
            </p>
          </div>
        )}
      </TooltipContent>
    </Tooltip>
  );
}
