"use client";

import { Loader2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  Legend,
} from "recharts";

import { ChartContainer } from "@/components/ui/chart";
import type { ChannelDashboardData } from "../../../../../types/metrics";
import { ChartInfoTooltip } from "../ChartInfoTooltip";
import { ChartSection } from "../../shared/ChartSection";

interface IgAudienceTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

interface FollowsDailyPoint {
  date: string;
  gained: number;
  lost: number;
  net: number;
}

export function IgAudienceTab({ data, isLoading }: IgAudienceTabProps) {
  if (isLoading)
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  if (!data)
    return (
      <div className="py-24 text-center text-sm text-muted-foreground">
        No hay datos disponibles
      </div>
    );

  const gainedSeries = data.timeSeries.find((ts) => ts.metricName === "ig_follows_gained");
  const lostSeries = data.timeSeries.find((ts) => ts.metricName === "ig_follows_lost");

  // Join gained + lost by date so both bars align. Show lost as negative so the
  // chart reads "above = new followers, below = unfollows, bar balance = net".
  const pointsByDate = new Map<string, FollowsDailyPoint>();
  for (const p of gainedSeries?.dataPoints ?? []) {
    pointsByDate.set(p.date, {
      date: p.date.slice(5),
      gained: p.value,
      lost: 0,
      net: p.value,
    });
  }
  for (const p of lostSeries?.dataPoints ?? []) {
    const existing = pointsByDate.get(p.date);
    if (existing) {
      existing.lost = -p.value;
      existing.net = existing.gained - p.value;
    } else {
      pointsByDate.set(p.date, {
        date: p.date.slice(5),
        gained: 0,
        lost: -p.value,
        net: -p.value,
      });
    }
  }
  const followsData = Array.from(pointsByDate.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );

  const totalGained = followsData.reduce((acc, d) => acc + d.gained, 0);
  const totalLost = followsData.reduce((acc, d) => acc + Math.abs(d.lost), 0);
  const totalNet = totalGained - totalLost;

  return (
    <div className="space-y-8">
      {followsData.length > 0 && (
        <ChartSection slug="seguidores-netos">
          <div className="space-y-2">
            <ChartInfoTooltip
              title="Crecimiento de Audiencia por Día"
              description="Barras verdes = nuevos seguidores ganados. Barras rojas (bajo cero) = seguidores perdidos. El balance diario es tu crecimiento neto."
            />
            <div className="flex items-baseline gap-4 text-xs">
              <span className="text-muted-foreground">
                Período:{" "}
                <span className="font-semibold tabular-nums text-foreground">
                  {totalNet >= 0 ? "+" : ""}
                  {totalNet.toLocaleString("en-US")}
                </span>{" "}
                netos
              </span>
              <span className="text-emerald-600">
                +{totalGained.toLocaleString("en-US")} ganados
              </span>
              <span className="text-red-600">−{totalLost.toLocaleString("en-US")} perdidos</span>
            </div>
            <ChartContainer
              config={{
                gained: { label: "Seguidores ganados", color: "hsl(142, 76%, 36%)" },
                lost: { label: "Seguidores perdidos", color: "hsl(0, 74%, 50%)" },
              }}
              className="h-[280px] w-full"
            >
              <BarChart data={followsData} stackOffset="sign">
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip
                  formatter={(value: number, key: string) => {
                    const label = key === "gained" ? "Ganados" : "Perdidos";
                    const rendered = key === "lost" ? Math.abs(value) : value;
                    return [rendered.toLocaleString("en-US"), label];
                  }}
                />
                <Legend />
                <Bar
                  dataKey="gained"
                  stackId="follows"
                  fill="var(--color-gained)"
                  radius={[2, 2, 0, 0]}
                />
                <Bar
                  dataKey="lost"
                  stackId="follows"
                  fill="var(--color-lost)"
                  radius={[0, 0, 2, 2]}
                />
              </BarChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
      <ChartSection slug="demografia">
        <div className="space-y-2">
          <ChartInfoTooltip
            title="Demografía de la Audiencia"
            description="Distribución por edad, género y ubicación de tus seguidores."
          />
          <div className="rounded-lg border bg-muted/30 p-6 text-center">
            <p className="text-sm text-muted-foreground">
              Datos demográficos disponibles próximamente
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Edad, género y ubicación de seguidores y cuentas engaged
            </p>
          </div>
        </div>
      </ChartSection>
    </div>
  );
}
