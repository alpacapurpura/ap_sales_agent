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

import { MetaAdsMiniFunnel } from "../../meta-ads/MetaAdsMiniFunnel";
import { ChartSection } from "../../shared/ChartSection";
import { ChartInfoTooltip } from "../ChartInfoTooltip";
import { IgOrganicGrowthIndicator } from "../IgOrganicGrowthIndicator";
import { IgOrganicHeroKpiGrid } from "../IgOrganicHeroKpiGrid";

import type { ChannelDashboardData } from "../../../../../types/metrics";

interface IgOverviewTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function IgOverviewTab({ data, isLoading }: IgOverviewTabProps) {
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

  const interactionsSeries = data.timeSeries.find((ts) => ts.metricName === "total_interactions");
  const viewsSeries = data.timeSeries.find((ts) => ts.metricName === "ig_views");

  const compositeData =
    viewsSeries?.dataPoints.map((vp) => {
      const interaction = interactionsSeries?.dataPoints.find((ip) => ip.date === vp.date);
      return { date: vp.date.slice(5), interactions: interaction?.value ?? 0, views: vp.value };
    }) ?? [];

  return (
    <div className="space-y-8">
      <ChartSection slug="kpis">
        <IgOrganicHeroKpiGrid kpis={data.kpis} timeSeries={data.timeSeries} />
      </ChartSection>
      {compositeData.length > 0 && (
        <ChartSection slug="engagement-vs-vistas">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Engagement vs Vistas"
              description="Compara las interacciones totales (barras) con las vistas de contenido (línea). Un ratio alto indica contenido de calidad."
            />
            <ChartContainer
              config={{
                interactions: { label: "Interacciones", color: "hsl(var(--chart-1))" },
                views: { label: "Vistas", color: "hsl(var(--chart-2))" },
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
                  dataKey="interactions"
                  fill="var(--color-interactions)"
                  radius={[2, 2, 0, 0]}
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="views"
                  stroke="var(--color-views)"
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
      <ChartSection slug="crecimiento">
        <IgOrganicGrowthIndicator kpis={data.kpis} />
      </ChartSection>
    </div>
  );
}
