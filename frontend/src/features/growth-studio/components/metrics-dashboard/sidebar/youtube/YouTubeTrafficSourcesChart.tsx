'use client';

import { Loader2, Sparkles } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts';
import { Badge } from '@/components/ui/badge';
import { useYoutubeTrafficSources } from '../../../../hooks/useYoutubeAnalytics';

const SOURCE_LABELS: Record<string, string> = {
  SUGGESTED: 'Recomendaciones YT',
  YT_SEARCH: 'Busqueda YT',
  SEARCH: 'Busqueda YT',
  BROWSE: 'Inicio YT',
  EXT_URL: 'Externo',
  NOTIFICATION: 'Notificaciones',
  PLAYLIST: 'Playlists',
  NO_LINK_OTHER: 'Otro',
  SUBSCRIBER: 'Suscripciones',
  END_SCREEN: 'Pantalla Final',
  ANNOTATION: 'Anotaciones',
  CAMPAIGN_CARD: 'Tarjetas',
  SHORTS: 'Shorts',
};

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return n.toLocaleString('es-ES');
}

interface YouTubeTrafficSourcesChartProps {
  enabled: boolean;
}

export function YouTubeTrafficSourcesChart({ enabled }: YouTubeTrafficSourcesChartProps) {
  const { data, isLoading, error } = useYoutubeTrafficSources(enabled);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return <p className="text-xs text-destructive py-4 text-center">Error al cargar tráfico: {error.message}</p>;
  }

  if (!data || data.length === 0) {
    return <p className="text-xs text-muted-foreground py-4 text-center">Sin datos de tráfico</p>;
  }

  const chartData = data
    .sort((a, b) => b.views - a.views)
    .slice(0, 8)
    .map(s => ({
      name: SOURCE_LABELS[s.insightTrafficSourceType] || s.insightTrafficSourceType,
      views: s.views,
      rawType: s.insightTrafficSourceType,
    }));

  const topSource = chartData[0];
  const isSuggested = topSource?.rawType === 'SUGGESTED';

  return (
    <div className="space-y-3">
      {isSuggested && (
        <Badge variant="outline" className="text-[10px] border-amber-500/50 text-amber-600 dark:text-amber-400">
          <Sparkles className="h-3 w-3 mr-1" />
          YouTube te esta recomendando
        </Badge>
      )}
      <ResponsiveContainer width="100%" height={chartData.length * 32 + 16}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 8, top: 0, bottom: 0 }}>
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="name"
            width={130}
            tick={{ fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: number) => [formatNumber(value), 'Vistas']}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="views" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {chartData.map((entry, idx) => (
              <Cell
                key={entry.name}
                fill={idx === 0 ? '#FF0000' : 'hsl(var(--muted-foreground) / 0.3)'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
