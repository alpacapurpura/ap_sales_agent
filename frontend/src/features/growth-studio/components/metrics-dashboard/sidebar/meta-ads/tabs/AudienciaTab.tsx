"use client";

import { Info, Loader2, Users } from "lucide-react";

import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useDemographics } from "../../../../../api/campaigns-api";
import type { DemographicSegment } from "../../../../../api/campaigns-api";
import type { ChannelDashboardData, MetaAdsPeriod } from "../../../../../types/metrics";
import { ChartSection } from "../../shared/ChartSection";
import { ReachFrequencySection } from "../ReachFrequencySection";

interface AudienciaTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

/** Determine the blue opacity class for an age bar relative to the max percentage. */
function getAgeBarClass(segment: DemographicSegment, maxPercentage: number): string {
  if (segment.percentage === maxPercentage) return "bg-blue-500/70";
  if (segment.percentage >= maxPercentage * 0.5) return "bg-blue-500/50";
  if (segment.percentage >= maxPercentage * 0.25) return "bg-blue-500/30";
  return "bg-blue-500/20";
}

/** Determine the emerald opacity class for a placement bar based on its position. */
function getPlacementBarClass(index: number): string {
  const classes = [
    "bg-emerald-500/50",
    "bg-emerald-500/40",
    "bg-emerald-500/30",
    "bg-emerald-500/20",
  ];
  return classes[index] ?? "bg-emerald-500/20";
}

/** Get the color class for a gender label. */
function getGenderColor(label: string): string {
  const lower = label.toLowerCase();
  if (lower === "femenino" || lower === "female") return "text-violet-400";
  if (lower === "masculino" || lower === "male") return "text-blue-400";
  return "text-zinc-200";
}

/** Small info icon with tooltip. */
function InfoTooltip({ text }: { text: string }) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Info className="h-3 w-3 text-muted-foreground/60 cursor-help shrink-0" />
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[280px] text-xs">
          {text}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function AudienciaTab({ data, isLoading, period }: AudienciaTabProps) {
  const { data: demographics } = useDemographics("meta-ads", period ?? "30d");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );
  }

  const maxAgePct = demographics?.age ? Math.max(...demographics.age.map((s) => s.percentage)) : 0;

  return (
    <div className="space-y-6">
      {/* Reach + Frequency */}
      <ChartSection slug="alcance-frecuencia">
        <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />
      </ChartSection>

      {/* Demographic Breakdown */}
      <ChartSection slug="demografia">
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Demografía de tu audiencia
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {/* Age Distribution */}
            {demographics?.age && demographics.age.length > 0 ? (
              <div className="rounded-xl border bg-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Distribución por edad
                  </h4>
                  <InfoTooltip text="Distribución de edad de las personas que ven tus anuncios. Usa esto para refinar tu targeting." />
                </div>
                <div className="space-y-2">
                  {demographics.age.map((seg) => {
                    const isDominant = seg.percentage === maxAgePct;
                    return (
                      <div key={seg.label} className="flex items-center gap-2">
                        <span className="text-[11px] text-muted-foreground w-10 text-right">
                          {seg.label}
                        </span>
                        <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                          <div
                            className={cn(
                              "h-full rounded-full flex items-center pl-2 text-[9px]",
                              getAgeBarClass(seg, maxAgePct),
                              isDominant && "font-semibold",
                            )}
                            style={{ width: `${Math.max(seg.percentage, 5)}%` }}
                          >
                            {seg.percentage.toFixed(0)}%{isDominant ? " \u2605" : ""}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
                <p className="font-medium text-xs">Distribución por edad</p>
                <p className="mt-1 text-[10px]">
                  Próximamente — desglose 18-24, 25-34, 35-44, 45-54, 55+
                </p>
              </div>
            )}

            {/* Gender Distribution */}
            {demographics?.gender && demographics.gender.length > 0 ? (
              <div className="rounded-xl border bg-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Distribución por género
                  </h4>
                  <InfoTooltip text="Distribución de género de tu audiencia alcanzada." />
                </div>
                <div className="flex items-center gap-4 py-6">
                  {demographics.gender.map((seg, idx) => (
                    <div key={seg.label} className="contents">
                      {idx > 0 && <div className="w-px h-12 bg-zinc-700" />}
                      <div className="flex-1 text-center">
                        <p
                          className={cn(
                            "text-3xl font-bold tabular-nums",
                            getGenderColor(seg.label),
                          )}
                        >
                          {seg.percentage.toFixed(0)}%
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">{seg.label}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
                <p className="font-medium text-xs">Distribución por género</p>
                <p className="mt-1 text-[10px]">Próximamente — femenino vs masculino</p>
              </div>
            )}

            {/* Placement Distribution */}
            {demographics?.placement && demographics.placement.length > 0 ? (
              <div className="rounded-xl border bg-card p-4">
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                    Dónde aparecen tus ads
                  </h4>
                  <InfoTooltip text="En qué ubicaciones de Meta aparecen tus anuncios. Feed = timeline, Stories = historias, Reels = videos cortos." />
                </div>
                <div className="space-y-2">
                  {demographics.placement.map((seg, idx) => (
                    <div key={seg.label} className="flex items-center gap-2">
                      <span
                        className="text-[11px] text-muted-foreground w-14 text-right truncate"
                        title={seg.label}
                      >
                        {seg.label}
                      </span>
                      <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full flex items-center pl-2 text-[9px] font-medium",
                            getPlacementBarClass(idx),
                          )}
                          style={{ width: `${Math.max(seg.percentage, 5)}%` }}
                        >
                          {seg.percentage.toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
                <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
                <p className="font-medium text-xs">Dónde aparecen tus ads</p>
                <p className="mt-1 text-[10px]">Próximamente — Feed, Stories, Reels, Otros</p>
              </div>
            )}
          </div>
        </div>
      </ChartSection>
    </div>
  );
}
