"use client";

import { Loader2, Users } from "lucide-react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip } from "recharts";

import { MetricInfoPopover } from "@/components/shared/MetricInfoPopover";
import { ChartContainer } from "@/components/ui/chart";
import { cn } from "@/lib/utils";

import { useMailAudience } from "../../../../../hooks/useMailDashboard";
import { ChartInfoTooltip } from "../../shared/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";

import type {
  EmailAudienceData,
  EmailEngagementSegment,
  SegmentTypeMatrixCell,
  EmailSourcePerformance,
  EngagementDecay,
  ActivityHeatmapCell,
} from "../../../../../types/mail-types";
import type { MetaAdsPeriod } from "../../../../../types/metrics";

interface MailAudienciaTabProps {
  period: MetaAdsPeriod;
}

// Segment configuration
const SEGMENT_CONFIG: Record<string, { emoji: string; borderColor: string; valueColor: string }> = {
  champions: {
    emoji: "\uD83C\uDFC6",
    borderColor: "border-t-emerald-500",
    valueColor: "text-emerald-600",
  },
  activos: {
    emoji: "\uD83D\uDC4D",
    borderColor: "border-t-blue-500",
    valueColor: "text-blue-600",
  },
  en_riesgo: {
    emoji: "\u26A0\uFE0F",
    borderColor: "border-t-amber-500",
    valueColor: "text-amber-600",
  },
  dormidos: {
    emoji: "\uD83D\uDE34",
    borderColor: "border-t-red-500",
    valueColor: "text-red-600",
  },
};

const DEFAULT_SEGMENT_CONFIG = {
  emoji: "\uD83D\uDCCA",
  borderColor: "border-t-muted-foreground",
  valueColor: "text-foreground",
};

// Heatmap helpers
function getHeatColor(value: number): string {
  if (value >= 10) return "bg-emerald-500/90";
  if (value >= 7) return "bg-emerald-500/70";
  if (value >= 5) return "bg-emerald-500/50";
  if (value >= 3) return "bg-emerald-500/30";
  if (value >= 1) return "bg-emerald-500/15";
  return "bg-muted";
}

const DAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];
const HOUR_LABELS = ["6-9", "9-12", "12-15", "15-18", "18-21", "21-24"];

// Decay stage colors
const DECAY_COLORS = ["text-emerald-500", "text-blue-500", "text-amber-500", "text-red-500"];
const DECAY_BAR_COLORS = ["bg-emerald-500", "bg-blue-500", "bg-amber-500", "bg-red-500"];

export function MailAudienciaTab({ period }: MailAudienciaTabProps) {
  const { data, isLoading } = useMailAudience(period);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
          <Users className="h-8 w-8 text-amber-500" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Sin datos de audiencia</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Los datos de audiencia se generarán cuando tengas suficiente historial de emails
            enviados.
          </p>
        </div>
      </div>
    );
  }

  // Compute at-risk + dormant percentage
  const atRiskAndDormant = data.segments
    .filter((s) => s.segmentName === "en_riesgo" || s.segmentName === "dormidos")
    .reduce((sum, s) => sum + s.percentage, 0);

  return (
    <div className="space-y-8 max-w-[1200px] mx-auto">
      {/* Section 1: Segment Cards */}
      {data.segments.length > 0 && (
        <ChartSection slug="segmentos-engagement">
          <SegmentCards segments={data.segments} />
          {atRiskAndDormant > 0 && (
            <div className="mt-3 rounded-md border-l-[3px] border-amber-500 bg-muted/30 px-3 py-2">
              <p className="text-xs text-muted-foreground">
                <span className="font-semibold text-amber-600">Alerta:</span>{" "}
                {atRiskAndDormant.toFixed(0)}% de tu lista está En Riesgo o Dormida. Una campaña de
                limpieza podría mejorar tu open rate inmediatamente.
              </p>
            </div>
          )}
        </ChartSection>
      )}

      {/* Section 2: Segment × Type Matrix + Engagement by Source */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {data.segmentTypeMatrix.length > 0 && (
          <ChartSection slug="matriz-segmento-tipo">
            <SegmentTypeMatrix matrix={data.segmentTypeMatrix} segments={data.segments} />
          </ChartSection>
        )}

        {data.sources.length > 0 && (
          <ChartSection slug="engagement-por-fuente">
            <EngagementBySource sources={data.sources} />
          </ChartSection>
        )}
      </div>

      {/* Section 3: Engagement Decay + Activity Heatmap */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {data.engagementDecay.length > 0 && (
          <ChartSection slug="ciclo-vida-engagement">
            <EngagementDecayCurve decay={data.engagementDecay} />
          </ChartSection>
        )}

        {data.activityHeatmap.length > 0 && (
          <ChartSection slug="mapa-actividad">
            <ActivityHeatmap heatmap={data.activityHeatmap} />
          </ChartSection>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SegmentCards({ segments }: { segments: EmailEngagementSegment[] }) {
  return (
    <div className="space-y-3">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
        Segmentos por Nivel de Engagement
      </p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {segments.map((segment) => {
          const config = SEGMENT_CONFIG[segment.segmentName] ?? DEFAULT_SEGMENT_CONFIG;

          return (
            <div
              key={segment.segmentName}
              className={cn(
                "rounded-lg border border-t-[3px] bg-card p-4 space-y-3",
                config.borderColor,
              )}
            >
              <div>
                <span className="text-lg">{config.emoji}</span>
                <p className="mt-1 text-sm font-semibold">{segment.label}</p>
              </div>

              <div>
                <p className={cn("text-2xl font-bold tabular-nums", config.valueColor)}>
                  {segment.count.toLocaleString("en-US")}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {segment.percentage.toFixed(0)}% de la lista
                </p>
              </div>

              <div className="space-y-1.5 pt-2 border-t border-border/50">
                <SegMetricRow
                  label="Open Rate"
                  value={`${segment.openRate.toFixed(1)}%`}
                  isGood={segment.openRate > 21.5}
                  isBad={segment.openRate < 5}
                />
                <SegMetricRow
                  label="Click Rate"
                  value={`${segment.clickRate.toFixed(1)}%`}
                  isGood={segment.clickRate > 2.3}
                  isBad={segment.clickRate < 0.5}
                />
                <SegMetricRow
                  label="CTOR"
                  value={`${segment.ctor.toFixed(1)}%`}
                  isGood={segment.ctor > 10.5}
                  isBad={segment.ctor < 3}
                />
                {segment.avgDaysInactive != null && (
                  <SegMetricRow
                    label="Días inactivo"
                    value={`${segment.avgDaysInactive} prom.`}
                    isBad={segment.avgDaysInactive > 60}
                  />
                )}
              </div>

              {segment.recommendedAction && (
                <div className="mt-2 rounded-md bg-muted/30 p-2">
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    <span className="font-semibold text-amber-500">Acción:</span>{" "}
                    {segment.recommendedAction}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SegMetricRow({
  label,
  value,
  isGood,
  isBad,
}: {
  label: string;
  value: string;
  isGood?: boolean;
  isBad?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          "font-semibold tabular-nums",
          isGood && "text-emerald-600",
          isBad && "text-red-500",
          !isGood && !isBad && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

function SegmentTypeMatrix({
  matrix,
  segments,
}: {
  matrix: SegmentTypeMatrixCell[];
  segments: EmailEngagementSegment[];
}) {
  // Build unique lists of campaign types and segment names from matrix data
  const campaignTypes = [...new Set(matrix.map((c) => c.campaignType))];
  const segmentNames = segments.map((s) => s.segmentName);

  const SEGMENT_VALUE_COLORS: Record<string, string> = {
    champions: "text-emerald-600",
    activos: "text-blue-500",
    en_riesgo: "text-amber-500",
    dormidos: "text-red-500",
  };

  function getCellValue(segmentName: string, campaignType: string): string {
    const cell = matrix.find(
      (c) => c.segmentName === segmentName && c.campaignType === campaignType,
    );
    return cell ? `${cell.openRate.toFixed(1)}%` : "-";
  }

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Preferencia por Tipo de Email"
        description="Open Rate promedio por segmento y tipo de campaña. Identifica qué contenido reactiva cada grupo."
      />
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-muted-foreground border-b">
              <th className="py-2 px-2 text-left font-medium" />
              {segmentNames.map((name) => {
                const config = SEGMENT_CONFIG[name];
                const seg = segments.find((s) => s.segmentName === name);
                return (
                  <th key={name} className="py-2 px-2 text-center font-medium">
                    {config?.emoji ?? ""} {seg?.label ?? name}
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {campaignTypes.map((type) => (
              <tr key={type} className="border-b border-border/20">
                <td className="py-2.5 px-2 text-xs text-muted-foreground capitalize">{type}</td>
                {segmentNames.map((name) => (
                  <td
                    key={`${type}-${name}`}
                    className={cn(
                      "py-2.5 px-2 text-center font-semibold tabular-nums",
                      SEGMENT_VALUE_COLORS[name] ?? "text-foreground",
                    )}
                  >
                    {getCellValue(name, type)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EngagementBySource({ sources }: { sources: EmailSourcePerformance[] }) {
  const maxSubscribers = Math.max(...sources.map((s) => s.subscriberCount), 1);

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Engagement por Fuente de Suscripción"
        description="De dónde vienen los suscriptores y cómo se comportan. Prioriza fuentes con alto engagement."
      />
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="text-muted-foreground border-b">
              <th className="py-2 px-2 text-left font-medium">Fuente</th>
              <th className="py-2 px-2 text-center font-medium">Suscriptores</th>
              <th className="py-2 px-2 text-center font-medium">Open Rate</th>
              <th className="py-2 px-2 text-center font-medium">Click Rate</th>
              <th className="py-2 px-2 text-center font-medium">% Champions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => (
              <tr
                key={source.source}
                className="border-b border-border/20 hover:bg-muted/20 transition-colors"
              >
                <td className="py-2.5 px-2">
                  <p className="text-xs font-semibold">{source.label}</p>
                </td>
                <td className="py-2.5 px-2 text-center tabular-nums">
                  {source.subscriberCount.toLocaleString("en-US")}
                  <span className="ml-1 text-[10px] text-muted-foreground">
                    ({source.percentage.toFixed(0)}%)
                  </span>
                </td>
                <td
                  className={cn(
                    "py-2.5 px-2 text-center font-semibold tabular-nums",
                    source.openRate > 25
                      ? "text-emerald-600"
                      : source.openRate < 15
                        ? "text-red-500"
                        : "text-foreground",
                  )}
                >
                  {source.openRate.toFixed(1)}%
                </td>
                <td
                  className={cn(
                    "py-2.5 px-2 text-center tabular-nums",
                    source.clickRate > 3 && "text-emerald-600",
                  )}
                >
                  {source.clickRate.toFixed(1)}%
                </td>
                <td className="py-2.5 px-2 text-center">
                  <div className="flex items-center justify-center gap-1.5">
                    <div className="relative h-1.5 w-14 rounded-full bg-muted overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full",
                          source.championsPct > 15
                            ? "bg-emerald-500"
                            : source.championsPct < 5
                              ? "bg-red-500"
                              : "bg-blue-500",
                        )}
                        style={{
                          width: `${Math.min(
                            (source.subscriberCount / maxSubscribers) * 100,
                            100,
                          )}%`,
                        }}
                      />
                    </div>
                    <span
                      className={cn(
                        "text-[11px] font-semibold tabular-nums",
                        source.championsPct > 15
                          ? "text-emerald-600"
                          : source.championsPct < 5
                            ? "text-red-500"
                            : "text-foreground",
                      )}
                    >
                      {source.championsPct.toFixed(0)}%
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EngagementDecayCurve({ decay }: { decay: EngagementDecay[] }) {
  const maxRate = Math.max(...decay.map((d) => d.openRate), 1);

  // Prepare data for AreaChart
  const chartData = decay.map((d) => ({
    label: d.periodLabel,
    openRate: d.openRate,
  }));

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Ciclo de Vida del Engagement"
        description="Cómo decae el engagement según la antigüedad del suscriptor. Los primeros 30 días son críticos."
      />

      {/* Stage bars */}
      <div className="flex gap-0 pt-1">
        {decay.map((stage, i) => {
          const widthPct = Math.max((stage.openRate / maxRate) * 100, 8);
          return (
            <div
              key={stage.periodLabel}
              className="flex-1 text-center px-1 relative border-r border-border/30 last:border-r-0"
            >
              <p
                className={cn(
                  "text-xl font-bold tabular-nums",
                  DECAY_COLORS[i % DECAY_COLORS.length],
                )}
              >
                {stage.openRate.toFixed(1)}%
              </p>
              <p className="text-[10px] text-muted-foreground mt-0.5">Open Rate</p>
              <p className="text-[10px] text-muted-foreground">{stage.periodLabel}</p>
              <div
                className={cn(
                  "h-1 rounded-full mx-auto mt-2",
                  DECAY_BAR_COLORS[i % DECAY_BAR_COLORS.length],
                )}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          );
        })}
      </div>

      {/* Area chart for visual curve */}
      {chartData.length > 1 && (
        <ChartContainer
          config={{
            openRate: { label: "Open Rate", color: "hsl(142, 71%, 45%)" },
          }}
          className="h-[120px] w-full mt-3"
        >
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="decayGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="label" className="text-xs" />
            <YAxis className="text-xs" unit="%" />
            <RechartsTooltip />
            <Area
              type="monotone"
              dataKey="openRate"
              stroke="var(--color-openRate)"
              fill="url(#decayGrad)"
              strokeWidth={2}
            />
          </AreaChart>
        </ChartContainer>
      )}

      {/* Insight */}
      {decay.length >= 2 && (
        <div className="rounded-md border-l-[3px] border-amber-500 bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-amber-600">Hallazgo:</span> El engagement cae{" "}
            {decay.length >= 2
              ? `${((1 - decay[1].openRate / decay[0].openRate) * 100).toFixed(0)}%`
              : "50%"}{" "}
            en los primeros 90 días. La automatización de onboarding es crítica.
          </p>
        </div>
      )}
    </div>
  );
}

function ActivityHeatmap({ heatmap }: { heatmap: ActivityHeatmapCell[] }) {
  // Find the best time slot
  let bestCell: ActivityHeatmapCell | null = null;
  for (const cell of heatmap) {
    if (!bestCell || cell.openRate > bestCell.openRate) {
      bestCell = cell;
    }
  }

  const bestDay = bestCell ? (DAY_LABELS[bestCell.dayOfWeek] ?? "N/A") : "N/A";
  const bestHour = bestCell?.hourBlock ?? "N/A";

  return (
    <div className="rounded-lg border bg-card p-5 space-y-3">
      <ChartInfoTooltip
        title="Mapa de Actividad Semanal"
        description="Cuándo abren tus suscriptores. Verde más intenso = mayor tasa de apertura."
      />

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div
          className="grid gap-[2px] text-[10px] min-w-[400px]"
          style={{ gridTemplateColumns: "60px repeat(7, 1fr)" }}
        >
          {/* Header row */}
          <div />
          {DAY_LABELS.map((day) => (
            <div key={day} className="text-center text-muted-foreground py-1 font-medium">
              {day}
            </div>
          ))}

          {/* Data rows */}
          {HOUR_LABELS.map((hour) => (
            <HeatmapRow key={hour} hour={hour} heatmap={heatmap} />
          ))}
        </div>
      </div>

      {/* Scale legend */}
      <div className="flex items-center gap-2 pt-1">
        <span className="text-[10px] text-muted-foreground">Menor</span>
        <div className="flex gap-[2px]">
          <div className="h-3 w-5 rounded-sm bg-muted" />
          <div className="h-3 w-5 rounded-sm bg-emerald-500/15" />
          <div className="h-3 w-5 rounded-sm bg-emerald-500/30" />
          <div className="h-3 w-5 rounded-sm bg-emerald-500/50" />
          <div className="h-3 w-5 rounded-sm bg-emerald-500/70" />
          <div className="h-3 w-5 rounded-sm bg-emerald-500/90" />
        </div>
        <span className="text-[10px] text-muted-foreground">Mayor</span>
      </div>

      {/* Insight */}
      {bestCell && (
        <div className="rounded-md border-l-[3px] border-blue-500 bg-muted/30 px-3 py-2">
          <p className="text-xs text-muted-foreground">
            <span className="font-semibold text-blue-600">Mejor momento:</span> {bestDay} {bestHour}{" "}
            ({bestCell.openRate.toFixed(1)}% apertura)
          </p>
        </div>
      )}
    </div>
  );
}

function HeatmapRow({ hour, heatmap }: { hour: string; heatmap: ActivityHeatmapCell[] }) {
  return (
    <>
      <div className="flex items-center text-muted-foreground pr-2 text-[10px]">{hour}</div>
      {DAY_LABELS.map((_, dayIdx) => {
        const cell = heatmap.find((c) => c.dayOfWeek === dayIdx && c.hourBlock === hour);
        const value = cell?.openRate ?? 0;

        return (
          <div
            key={`${dayIdx}-${hour}`}
            className={cn("flex items-center justify-center rounded-sm py-2", getHeatColor(value))}
            title={`${DAY_LABELS[dayIdx]} ${hour}: ${value.toFixed(1)}%`}
          >
            <span
              className={cn(
                "text-[9px] font-semibold",
                value >= 10
                  ? "text-white"
                  : value >= 1
                    ? "text-foreground/70"
                    : "text-muted-foreground/50",
              )}
            >
              {value > 0 ? `${value.toFixed(0)}%` : ""}
            </span>
          </div>
        );
      })}
    </>
  );
}
