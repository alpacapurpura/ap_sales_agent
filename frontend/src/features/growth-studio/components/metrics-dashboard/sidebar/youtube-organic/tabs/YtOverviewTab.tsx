"use client";

import { Loader2 } from "lucide-react";
import {
  Bar,
  ComposedChart,
  CartesianGrid,
  Line,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
} from "recharts";

import { ChartContainer } from "@/components/ui/chart";
import type { ChannelDashboardData } from "../../../../../types/metrics";
import { YouTubeHeroKpiGrid } from "../YouTubeHeroKpiGrid";
import { MetaAdsMiniFunnel } from "../../meta-ads/MetaAdsMiniFunnel";
import { YouTubeSubscriberGrowth } from "../YouTubeSubscriberGrowth";
import { ChartInfoTooltip } from "../../ig-organic/ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";

interface YtOverviewTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function YtOverviewTab({ data, isLoading }: YtOverviewTabProps) {
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

  const viewsSeries = data.timeSeries.find((ts) => ts.metricName === "views");
  const watchTimeSeries = data.timeSeries.find((ts) => ts.metricName === "watch_time_minutes");

  const compositeData =
    viewsSeries?.dataPoints.map((vp) => {
      const wt = watchTimeSeries?.dataPoints.find((wp) => wp.date === vp.date);
      return {
        date: vp.date.slice(5),
        views: vp.value,
        watchTime: wt?.value ?? 0,
      };
    }) ?? [];

  return (
    <div className="space-y-8">
      <ChartSection slug="kpis">
        <YouTubeHeroKpiGrid kpis={data.kpis} timeSeries={data.timeSeries} />
      </ChartSection>

      {compositeData.length > 0 && (
        <ChartSection slug="vistas-vs-minutos">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Vistas vs Minutos Vistos"
              description="Compara las vistas totales (barras) con el tiempo de visualizaci&oacute;n (l&iacute;nea). El algoritmo de YouTube prioriza watch time sobre views."
            />
            <ChartContainer
              config={{
                views: { label: "Vistas", color: "hsl(var(--chart-1))" },
                watchTime: { label: "Minutos Vistos", color: "hsl(var(--chart-2))" },
              }}
              className="h-[250px] w-full"
            >
              <ComposedChart data={compositeData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis yAxisId="left" className="text-xs" />
                <YAxis yAxisId="right" orientation="right" className="text-xs" />
                <RechartsTooltip />
                <Bar
                  yAxisId="left"
                  dataKey="views"
                  fill="var(--color-views)"
                  radius={[2, 2, 0, 0]}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="watchTime"
                  stroke="var(--color-watchTime)"
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}

      <ChartSection slug="embudo">
        <MetaAdsMiniFunnel steps={data.funnel.steps} />
      </ChartSection>
      <ChartSection slug="crecimiento-suscriptores">
        <YouTubeSubscriberGrowth kpis={data.kpis} />
      </ChartSection>
    </div>
  );
}
