'use client';

import { memo, useMemo } from 'react';
import type { ChannelMetric } from '../../../types/metrics';
import { getChannelColor } from '../../../lib/channelIcons';

interface CaptureBreakdownChartProps {
  channels: ChannelMetric[];
  isLoading: boolean;
}

interface ChartEntry {
  name: string;
  slug: string;
  value: number;
  pct: string;
  fill: string;
}

export const CaptureBreakdownChart = memo(function CaptureBreakdownChart({ channels, isLoading }: CaptureBreakdownChartProps) {
  const { chartData, total } = useMemo(() => {
    if (!channels.length) {
      return { chartData: [] as ChartEntry[], total: 0 };
    }

    const withLeads = channels
      .map((ch) => ({
        slug: ch.slug,
        name: ch.name,
        leads: ch.metrics.find((m) => m.name === 'leads')?.value ?? 0,
        color: getChannelColor(ch.slug),
      }))
      .filter((ch) => ch.leads > 0)
      .sort((a, b) => b.leads - a.leads);

    const totalLeads = withLeads.reduce((s, ch) => s + ch.leads, 0);

    const data: ChartEntry[] = withLeads.map((ch) => ({
      name: ch.name,
      slug: ch.slug,
      value: ch.leads,
      pct: totalLeads > 0 ? ((ch.leads / totalLeads) * 100).toFixed(1) : '0',
      fill: ch.color,
    }));

    return { chartData: data, total: totalLeads };
  }, [channels]);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[300px] animate-pulse flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Cargando fuentes...</span>
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-[300px] flex items-center justify-center">
        <span className="text-muted-foreground text-sm">Sin datos de captura</span>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-foreground">Leads por Fuente</h4>
        <span className="text-xs text-muted-foreground">{total} total</span>
      </div>
      <div className="space-y-2">
        {chartData.map((entry) => {
          const maxVal = chartData[0].value;
          const barPct = maxVal > 0 ? (entry.value / maxVal) * 100 : 0;
          return (
            <div key={entry.slug} className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground w-20 text-right shrink-0 truncate">
                {entry.name}
              </span>
              <div className="flex-1 bg-muted rounded-full h-5 overflow-hidden">
                <div
                  className="h-full rounded-full flex items-center pl-2 transition-all duration-500"
                  style={{
                    width: `${Math.max(barPct, 4)}%`,
                    backgroundColor: entry.fill,
                    opacity: 0.8,
                  }}
                >
                  {barPct > 15 && (
                    <span className="text-[10px] font-semibold text-white">{entry.value}</span>
                  )}
                </div>
              </div>
              {barPct <= 15 && (
                <span className="text-xs font-semibold tabular-nums text-foreground w-8">{entry.value}</span>
              )}
              <span className="text-[10px] text-muted-foreground w-10 text-right">{entry.pct}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
});
