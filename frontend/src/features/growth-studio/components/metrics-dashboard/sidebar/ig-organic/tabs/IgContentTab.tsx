'use client';

import { Loader2 } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Cell, Pie, PieChart } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { ChartInfoTooltip } from '../ChartInfoTooltip';

interface IgContentTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

const ENGAGEMENT_COLORS = ['hsl(var(--chart-1))', 'hsl(var(--chart-2))', 'hsl(var(--chart-3))', 'hsl(var(--chart-4))'];
const ENGAGEMENT_METRICS = ['ig_likes', 'ig_comments', 'ig_shares', 'ig_saves'];
const ENGAGEMENT_LABELS: Record<string, string> = { ig_likes: 'Likes', ig_comments: 'Comentarios', ig_shares: 'Compartidos', ig_saves: 'Guardados' };

export function IgContentTab({ data, isLoading }: IgContentTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const seriesMap = new Map<string, Record<string, string | number>>();
  for (const metric of ENGAGEMENT_METRICS) {
    const ts = data.timeSeries.find(s => s.metricName === metric);
    if (!ts) continue;
    for (const dp of ts.dataPoints) {
      const entry = seriesMap.get(dp.date) ?? ({ date: dp.date } as Record<string, string | number>);
      entry[metric] = dp.value;
      seriesMap.set(dp.date, entry);
    }
  }
  const stackedData = Array.from(seriesMap.values())
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map(d => ({ ...d, date: String(d.date).slice(5) }));

  const donutData = ENGAGEMENT_METRICS.map(metric => {
    const ts = data.timeSeries.find(s => s.metricName === metric);
    const total = ts?.dataPoints.reduce((sum, p) => sum + p.value, 0) ?? 0;
    return { name: ENGAGEMENT_LABELS[metric] ?? metric, value: total };
  }).filter(d => d.value > 0);

  return (
    <div className="space-y-8">
      {stackedData.length > 0 && (
        <div className="space-y-2">
          <ChartInfoTooltip title="Desglose de Engagement Diario" description="Distribución diaria de likes, comentarios, compartidos y guardados." />
          <ChartContainer
            config={{ ig_likes: { label: 'Likes', color: ENGAGEMENT_COLORS[0] }, ig_comments: { label: 'Comentarios', color: ENGAGEMENT_COLORS[1] }, ig_shares: { label: 'Compartidos', color: ENGAGEMENT_COLORS[2] }, ig_saves: { label: 'Guardados', color: ENGAGEMENT_COLORS[3] } }}
            className="h-[280px] w-full"
          >
            <BarChart data={stackedData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis dataKey="date" className="text-xs" />
              <YAxis className="text-xs" />
              <RechartsTooltip />
              {ENGAGEMENT_METRICS.map((metric, i) => (
                <Bar key={metric} dataKey={metric} stackId="engagement" fill={ENGAGEMENT_COLORS[i]} radius={i === ENGAGEMENT_METRICS.length - 1 ? [2, 2, 0, 0] : undefined} />
              ))}
            </BarChart>
          </ChartContainer>
        </div>
      )}
      {donutData.length > 0 && (
        <div className="space-y-2">
          <ChartInfoTooltip title="Distribución del Engagement" description="Proporción de cada tipo de interacción. Guardados y compartidos indican contenido de alto valor." />
          <div className="flex items-center gap-6">
            <ChartContainer config={{}} className="h-[200px] w-[200px] !aspect-auto">
              <PieChart>
                <Pie data={donutData} innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                  {donutData.map((_, i) => (<Cell key={i} fill={ENGAGEMENT_COLORS[i % ENGAGEMENT_COLORS.length]} />))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ChartContainer>
            <div className="space-y-2">
              {donutData.map((d, i) => {
                const total = donutData.reduce((s, e) => s + e.value, 0);
                const pct = total > 0 ? ((d.value / total) * 100).toFixed(1) : '0.0';
                return (
                  <div key={d.name} className="flex items-center gap-2 text-sm">
                    <span className="h-3 w-3 rounded-sm shrink-0" style={{ backgroundColor: ENGAGEMENT_COLORS[i % ENGAGEMENT_COLORS.length] }} />
                    <span className="text-muted-foreground">{d.name}</span>
                    <span className="font-medium tabular-nums ml-auto">{pct}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
