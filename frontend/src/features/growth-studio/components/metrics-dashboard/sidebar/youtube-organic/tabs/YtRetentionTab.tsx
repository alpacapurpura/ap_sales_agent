"use client";

import { Loader2 } from "lucide-react";
import { Line, LineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip } from "recharts";

import { ChartContainer } from "@/components/ui/chart";

import { MetricInfoCard } from "../../../channel-widgets/KpiTooltip";
import { ChartInfoTooltip } from "../../ig-organic/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";

import type { ChannelDashboardData, MetricKpiData } from "../../../../../types/metrics";

interface YtRetentionTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const RETENTION_METRICS = ["avg_view_duration", "avg_view_percentage", "watch_time_minutes"];

function formatRetentionValue(kpi: MetricKpiData): string {
  if (kpi.unit === "percentage") return `${kpi.currentValue.toFixed(1)}%`;
  if (kpi.unit === "seconds") {
    const mins = Math.floor(kpi.currentValue / 60);
    const secs = Math.round(kpi.currentValue % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  }
  if (Math.abs(kpi.currentValue) >= 1000) return `${(kpi.currentValue / 1000).toFixed(1)}k`;
  return kpi.currentValue.toLocaleString("en-US");
}

/**
 *
 */
export function YtRetentionTab({ data, isLoading }: YtRetentionTabProps) {
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

  const retentionKpis = RETENTION_METRICS.map((name) =>
    data.kpis.find((k) => k.metricName === name),
  ).filter((k): k is MetricKpiData => k != null);

  // Build retention trend chart
  const watchTimeSeries = data.timeSeries.find((ts) => ts.metricName === "watch_time_minutes");
  const avgViewPctSeries = data.timeSeries.find((ts) => ts.metricName === "avg_view_percentage");

  const dateMap = new Map<string, Record<string, string | number>>();
  for (const series of [watchTimeSeries, avgViewPctSeries].filter(
    (s): s is NonNullable<typeof s> => s != null,
  )) {
    for (const point of series.dataPoints) {
      const key = point.date.slice(5);
      const existing = dateMap.get(key) ?? { date: key };
      existing[series.metricName] = point.value;
      dateMap.set(key, existing);
    }
  }
  const chartData = Array.from(dateMap.values());

  return (
    <div className="space-y-8">
      {/* Retention KPI cards */}
      <ChartSection slug="kpis-retencion">
        <div className="grid grid-cols-3 gap-4">
          {retentionKpis.map((kpi) => {
            const deltaIsPositive =
              kpi.deltaPct != null && (kpi.higherIsBetter ? kpi.deltaPct >= 0 : kpi.deltaPct <= 0);

            return (
              <div key={kpi.metricName} className="rounded-lg border bg-card p-4 space-y-1">
                <MetricInfoCard metricName={kpi.metricName}>
                  <p className="text-xs text-muted-foreground">{kpi.displayName}</p>
                </MetricInfoCard>
                <p className="text-2xl font-semibold tabular-nums">{formatRetentionValue(kpi)}</p>
                {kpi.deltaPct != null && (
                  <p
                    className={`text-xs font-medium ${deltaIsPositive ? "text-emerald-600" : "text-red-600"}`}
                  >
                    {kpi.deltaPct > 0 ? "+" : ""}
                    {kpi.deltaPct.toFixed(1)}% vs anterior
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </ChartSection>

      {/* Retention trend chart */}
      {chartData.length > 0 && (
        <ChartSection slug="tendencia-retencion">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Tendencia de Retenci&oacute;n"
              description="El algoritmo de YouTube prioriza watch time sobre views. Una retenci&oacute;n alta indica que tu contenido mantiene la atenci&oacute;n."
            />
            <ChartContainer
              config={{
                watch_time_minutes: { label: "Minutos Vistos", color: "hsl(var(--chart-1))" },
                avg_view_percentage: { label: "% Retenci&oacute;n", color: "hsl(var(--chart-2))" },
              }}
              className="h-[250px] w-full"
            >
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis yAxisId="left" className="text-xs" />
                <YAxis yAxisId="right" orientation="right" className="text-xs" domain={[0, 100]} />
                <RechartsTooltip />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="watch_time_minutes"
                  stroke="var(--color-watch_time_minutes)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="avg_view_percentage"
                  stroke="var(--color-avg_view_percentage)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
    </div>
  );
}
