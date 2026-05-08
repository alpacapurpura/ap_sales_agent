"use client";

import { memo, useMemo } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatTenantDate } from "@/lib/format-date";

import { getChannelColor } from "@/lib/constants/channel-colors";

import type { StageTimeSeries } from "../../../types/metrics";

interface AttractionTrendChartProps {
  timeSeries: StageTimeSeries | undefined;
  isLoading: boolean;
}

/** Max channels to show individually — rest grouped as "otros". */
const MAX_CHANNELS = 6;

export const AttractionTrendChart = memo(function AttractionTrendChart({
  timeSeries,
  isLoading,
}: AttractionTrendChartProps) {
  const { timezone } = useTenantLocale();
  const { chartData, channelKeys, chartConfig } = useMemo(() => {
    if (!timeSeries?.dataPoints.length || !timeSeries.channelsPresent.length) {
      return { chartData: [], channelKeys: [] as string[], chartConfig: {} as ChartConfig };
    }

    // Sort channels by total volume desc
    const sorted = [...timeSeries.channelsPresent].sort(
      (a, b) => (timeSeries.periodTotals[b.slug] ?? 0) - (timeSeries.periodTotals[a.slug] ?? 0),
    );

    const top = sorted.slice(0, MAX_CHANNELS);
    const rest = sorted.slice(MAX_CHANNELS);
    const hasOtros = rest.length > 0;

    // Build keys list
    const keys = top.map((ch) => ch.slug);
    if (hasOtros) keys.push("otros");

    // Build chart config
    const cfg: ChartConfig = {};
    for (const ch of top) {
      cfg[ch.slug] = {
        label: ch.name,
        color: getChannelColor(ch.slug),
      };
    }
    if (hasOtros) {
      cfg.otros = { label: "Otros", color: "#9CA3AF" };
    }

    // Build flat chart data
    const data = timeSeries.dataPoints.map((dp) => {
      const row: Record<string, string | number> = {
        date: dp.date,
      };
      for (const ch of top) {
        row[ch.slug] = dp.channels[ch.slug] ?? 0;
      }
      if (hasOtros) {
        row.otros = rest.reduce((sum, ch) => sum + (dp.channels[ch.slug] ?? 0), 0);
      }
      return row;
    });

    return { chartData: data, channelKeys: keys, chartConfig: cfg };
  }, [timeSeries]);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[350px] animate-pulse flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Cargando tendencia...</span>
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[350px] flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Sin datos de tendencia disponibles</span>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h4 className="text-sm font-semibold text-foreground mb-3">Tendencia de Alcance</h4>
      <ChartContainer config={chartConfig} className="h-[280px] w-full !aspect-auto">
        <AreaChart data={chartData} accessibilityLayer>
          <CartesianGrid vertical={false} />
          <XAxis
            dataKey="date"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
            tickFormatter={(v: string) => {
              return formatTenantDate(`${v}T00:00:00`, timezone, "MMM d");
            }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v))}
            width={45}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                labelFormatter={(val) => {
                  return formatTenantDate(`${String(val)}T00:00:00`, timezone, "eee, d MMM");
                }}
              />
            }
          />
          <ChartLegend content={<ChartLegendContent />} />
          {channelKeys.map((key) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stackId="1"
              fill={`var(--color-${key})`}
              stroke={`var(--color-${key})`}
              fillOpacity={0.4}
              strokeWidth={1.5}
            />
          ))}
        </AreaChart>
      </ChartContainer>
    </div>
  );
});
