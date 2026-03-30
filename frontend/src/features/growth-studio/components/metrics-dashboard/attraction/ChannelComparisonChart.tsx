'use client';

import { useMemo } from 'react';
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, Cell } from 'recharts';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import type { StageTimeSeries } from '../../../types/metrics';
import { getChannelColor } from '../../../config/channel-chart-config';

interface ChannelComparisonChartProps {
  timeSeries: StageTimeSeries | undefined;
  isLoading: boolean;
}

export function ChannelComparisonChart({ timeSeries, isLoading }: ChannelComparisonChartProps) {
  const { chartData, chartConfig } = useMemo(() => {
    if (!timeSeries?.channelsPresent.length) {
      return { chartData: [], chartConfig: {} as ChartConfig };
    }

    // Sort by period totals desc
    const sorted = [...timeSeries.channelsPresent]
      .map((ch) => ({
        slug: ch.slug,
        name: ch.name,
        value: timeSeries.periodTotals[ch.slug] ?? 0,
        color: getChannelColor(ch.slug),
      }))
      .filter((ch) => ch.value > 0)
      .sort((a, b) => b.value - a.value);

    const total = sorted.reduce((s, ch) => s + ch.value, 0);

    const data = sorted.map((ch) => ({
      name: ch.name,
      slug: ch.slug,
      value: ch.value,
      pct: total > 0 ? ((ch.value / total) * 100).toFixed(1) : '0',
      fill: ch.color,
    }));

    const cfg: ChartConfig = {};
    for (const ch of sorted) {
      cfg[ch.slug] = { label: ch.name, color: ch.color };
    }
    cfg['value'] = { label: 'Total' };

    return { chartData: data, chartConfig: cfg };
  }, [timeSeries]);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[350px] animate-pulse flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Cargando canales...</span>
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[350px] flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Sin datos de canales disponibles</span>
      </div>
    );
  }

  // Dynamic height based on number of bars
  const barHeight = Math.max(280, chartData.length * 40);

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h4 className="text-sm font-semibold text-foreground mb-3">Comparacion por Canal</h4>
      <ChartContainer config={chartConfig} className="w-full !aspect-auto" style={{ height: barHeight }}>
        <BarChart
          data={chartData}
          layout="vertical"
          accessibilityLayer
          margin={{ left: 0, right: 16 }}
        >
          <CartesianGrid horizontal={false} />
          <YAxis
            dataKey="name"
            type="category"
            tickLine={false}
            axisLine={false}
            width={120}
            tick={{ fontSize: 11 }}
          />
          <XAxis
            type="number"
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : String(v)}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                formatter={(value, _name, item) => (
                  <span>
                    {Number(value).toLocaleString('es-ES')}
                    <span className="ml-1 text-muted-foreground">
                      ({item.payload.pct}%)
                    </span>
                  </span>
                )}
                hideLabel
              />
            }
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={24}>
            {chartData.map((entry) => (
              <Cell key={entry.slug} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ChartContainer>
    </div>
  );
}
