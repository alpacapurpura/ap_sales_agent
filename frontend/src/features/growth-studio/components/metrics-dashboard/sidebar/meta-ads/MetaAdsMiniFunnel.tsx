"use client";

/**
 * MetaAdsMiniFunnel — 5-step vertical funnel (Impresiones → Clics → Landing →
 * Leads → Conversiones).
 *
 * Reliability of data representation is the #1 attribute here. Every rule is
 * documented in the UI-SPEC (§6) and enforced by tests.
 *
 * Highlights:
 *  - Bar width is proportional to the first step (so "Impresiones" == 100%).
 *    A 2% floor keeps non-zero bars visible even when the ratio is tiny.
 *  - Conversion rate between consecutive steps is rendered inline (no hover
 *    needed) with a color ramp (emerald → red) and a tooltip that spells it
 *    out in full Spanish text.
 *  - Each step has a Shadcn Tooltip with the metric's label, technical name,
 *    formatted value, conversion rate and a short explanation.
 *  - Empty state varies with the active filter ("all" / "offer" / "branding"
 *    / "unassigned") — we never render an ambiguous "no data" screen.
 *  - Accessible: `role="list"`, narrative `aria-label` per step, tooltips
 *    open on keyboard focus (Radix default).
 */

import { ArrowDown, HelpCircle, Inbox } from "lucide-react";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { RESUMEN_TOOLTIPS } from "./copy/tooltips";

import type { FunnelStep } from "../../../../types/metrics";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type MetaAdsMiniFunnelFilter = "all" | "offer" | "branding" | "unassigned";

export interface MetaAdsMiniFunnelProps {
  steps: FunnelStep[];
  /**
   * Active filter on the parent tab. Controls the copy of the empty state so
   * the user understands WHY the funnel is empty (no pixel events vs. no
   * branding impressions vs. unassigned campaigns).
   */
  filter?: MetaAdsMiniFunnelFilter;
}

// ---------------------------------------------------------------------------
// Color ramp
// ---------------------------------------------------------------------------

/**
 * Thresholds come from UI-SPEC §6 "Color ramp por tasa de conversión". They
 * are an intentional approximation — real healthy ranges depend on the metric
 * (CTR lives at 1–3%, landing→lead at 10–30%). V1 uses this single ramp for
 * simplicity; logged as tech debt for per-step calibration in V2.
 */
const RATE_RAMP = [
  { min: 25, text: "text-emerald-500", bar: "bg-emerald-500" },
  { min: 10, text: "text-lime-500", bar: "bg-lime-500" },
  { min: 3, text: "text-amber-500", bar: "bg-amber-500" },
  { min: 0.5, text: "text-orange-500", bar: "bg-orange-500" },
  { min: -Infinity, text: "text-red-500", bar: "bg-red-500" },
] as const;

function rampFor(rate: number): { text: string; bar: string } {
  for (const bucket of RATE_RAMP) {
    if (rate >= bucket.min) return { text: bucket.text, bar: bucket.bar };
  }
  // Unreachable — the last bucket matches -Infinity.
  return { text: RATE_RAMP[RATE_RAMP.length - 1].text, bar: RATE_RAMP[RATE_RAMP.length - 1].bar };
}

// ---------------------------------------------------------------------------
// Per-step tooltip key — maps a metricName to the RESUMEN_TOOLTIPS entry that
// explains this step to the user.
// ---------------------------------------------------------------------------

function tooltipKeyFor(metricName: string): keyof typeof RESUMEN_TOOLTIPS | null {
  const name = metricName.toLowerCase();
  if (name.includes("impression")) return "funnel_impressions";
  if (name.includes("landing")) return "funnel_landing";
  if (name.includes("click")) return "funnel_clicks";
  if (name.includes("lead")) return "funnel_leads";
  if (name.includes("conversion") || name.includes("purchase")) return "funnel_conversions";
  return null;
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

const EMPTY_COPY: Record<MetaAdsMiniFunnelFilter, string> = {
  all: "Sin actividad medible en este período y filtro.",
  offer: "Esta offer aún no tiene campañas asignadas o no reportó eventos en el período.",
  branding: "Sin impresiones de branding en este período.",
  unassigned: "Las campañas sin asignar no reportaron eventos en el período.",
};

function EmptyFunnel({ filter }: { filter: MetaAdsMiniFunnelFilter }) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-md bg-muted/30 py-8 px-4 text-center"
      role="status"
      aria-label="Embudo sin datos"
    >
      <Inbox className="h-8 w-8 text-muted-foreground/40" aria-hidden="true" />
      <p className="mt-2 text-sm text-muted-foreground">{EMPTY_COPY[filter]}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

/**
 *
 */
export function MetaAdsMiniFunnel({ steps, filter = "all" }: MetaAdsMiniFunnelProps) {
  if (steps.length === 0) return null;

  // Empty state: every step is exactly 0.
  const allZero = steps.every((s) => s.value === 0);
  if (allZero) return <EmptyFunnel filter={filter} />;

  // Reference: first step drives bar width. Fall back to 1 to avoid /0.
  const firstValue = steps[0]?.value ?? 0;
  const denominator = firstValue > 0 ? firstValue : 1;

  return (
    // Local TooltipProvider keeps the component self-contained so it works
    // when rendered outside a parent that already provides one (e.g.
    // ChannelOverviewPanel, WebsiteOverviewPanel, YouTubeDashboard). Nested
    // providers are a no-op in Radix so ResumenTab continues to work.
    <TooltipProvider delayDuration={250}>
      <div role="list" aria-label="Embudo de conversión" className="space-y-3">
        {steps.map((step, i) => {
          const previous = i > 0 ? steps[i - 1] : null;
          const rate = step.conversionRate;
          const hasRate = i > 0 && rate != null && previous != null && previous.value > 0;

          // Bar width: proportional to the first step. Non-zero values get a 2%
          // floor so they are always visible. Zero stays at 0%.
          const widthPct = step.value === 0 ? 0 : Math.max((step.value / denominator) * 100, 2);

          // Color ramp for this step's bar: the first step is always neutral
          // blue (nothing to compare against); subsequent steps reuse the rate
          // ramp so "red rate → red bar" reads consistently.
          const barColor =
            i === 0 ? "bg-blue-500" : hasRate ? rampFor(rate).bar : "bg-muted-foreground/30";

          const rateColor = hasRate ? rampFor(rate).text : "text-muted-foreground";
          const tooltipKey = tooltipKeyFor(step.metricName);
          const tooltipContent = tooltipKey ? RESUMEN_TOOLTIPS[tooltipKey] : null;

          const formattedValue = step.value.toLocaleString("en-US");
          const ariaRate = hasRate
            ? `, tasa del ${rate.toFixed(1)}% desde ${previous?.label ?? "paso anterior"}`
            : "";
          const stepAriaLabel = `${step.label}: ${formattedValue}${ariaRate}`;

          return (
            <div key={`${step.metricName}-${i}`}>
              {/* Rate row — shown BETWEEN steps, above the current one. */}
              {hasRate && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div
                      className={cn(
                        "-my-1 flex items-center gap-1 pl-[calc(30%+0.5rem)] text-[10px] font-medium tabular-nums",
                        rateColor,
                      )}
                      aria-hidden="true"
                    >
                      <ArrowDown className="h-3 w-3" />
                      <span>{rate.toFixed(1)}%</span>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="right" className="max-w-xs">
                    <p className="text-xs">
                      Tasa de conversión entre{" "}
                      <span className="font-semibold">{previous?.label}</span> y{" "}
                      <span className="font-semibold">{step.label}</span>:{" "}
                      <span className="font-semibold">{rate.toFixed(2)}%</span>
                    </p>
                  </TooltipContent>
                </Tooltip>
              )}

              {/* Step row */}
              <div
                role="listitem"
                aria-label={stepAriaLabel}
                tabIndex={0}
                className="group grid grid-cols-[30%_1fr_auto] items-center gap-3 rounded-sm text-xs focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                {/* Label + optional help icon (Tooltip trigger) */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex items-center gap-1 text-muted-foreground">
                      <span className="truncate">{step.label}</span>
                      {tooltipContent && (
                        <HelpCircle
                          className="h-3 w-3 shrink-0 opacity-0 transition-opacity group-hover:opacity-60 group-focus-visible:opacity-60"
                          aria-hidden="true"
                        />
                      )}
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs space-y-1">
                    <p className="text-xs font-semibold">{step.label}</p>
                    <p className="font-mono text-[10px] text-muted-foreground">{step.metricName}</p>
                    <p className="text-xs tabular-nums">
                      Valor: <span className="font-semibold">{formattedValue}</span>
                    </p>
                    {hasRate && (
                      <p className="text-xs">
                        Tasa vs {previous?.label}:{" "}
                        <span className="font-semibold">{rate.toFixed(2)}%</span>
                      </p>
                    )}
                    {tooltipContent && (
                      <p className="pt-1 text-[11px] leading-snug text-muted-foreground">
                        {tooltipContent.body}
                      </p>
                    )}
                  </TooltipContent>
                </Tooltip>

                {/* Progress bar */}
                <div
                  className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
                  aria-hidden="true"
                >
                  <div
                    className={cn("h-full rounded-full transition-all", barColor)}
                    // Width must be computed at render time: Tailwind cannot
                    // express arbitrary per-step percentages at build time.
                    style={{ width: `${widthPct}%` }}
                  />
                </div>

                {/* Value */}
                <span
                  className={cn(
                    "font-semibold tabular-nums text-foreground",
                    step.value === 0 && "text-muted-foreground",
                  )}
                >
                  {formattedValue}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </TooltipProvider>
  );
}
