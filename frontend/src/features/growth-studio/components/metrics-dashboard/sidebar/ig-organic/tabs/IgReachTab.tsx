'use client';

import { Loader2 } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { ChartInfoTooltip } from '../ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';

interface IgReachTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function IgReachTab({ data, isLoading }: IgReachTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const viewsSeries = data.timeSeries.find(ts => ts.metricName === 'ig_views');
  const viewsData = viewsSeries?.dataPoints.map(p => ({ date: p.date.slice(5), views: p.value })) ?? [];

  const profileTapsSeries = data.timeSeries.find(ts => ts.metricName === 'ig_profile_links_taps');
  const profileTapsData = profileTapsSeries?.dataPoints.map(p => ({ date: p.date.slice(5), taps: p.value })) ?? [];

  return (
    <div className="space-y-8">
      {viewsData.length > 0 && (
        <ChartSection slug="tendencia-vistas">
          <div className="space-y-2">
            <ChartInfoTooltip title="Tendencia de Vistas" description="Número de veces que tu contenido fue reproducido o mostrado." />
            <ChartContainer config={{ views: { label: 'Vistas', color: 'hsl(var(--chart-1))' } }} className="h-[250px] w-full">
              <LineChart data={viewsData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Line type="monotone" dataKey="views" stroke="var(--color-views)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
      {profileTapsData.length > 0 && (
        <ChartSection slug="taps-perfil">
          <div className="space-y-2">
            <ChartInfoTooltip title="Taps en Perfil" description="Clics en el link del perfil. Métrica clave de conversión." />
            <ChartContainer config={{ taps: { label: 'Taps en Perfil', color: 'hsl(var(--chart-3))' } }} className="h-[200px] w-full">
              <BarChart data={profileTapsData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Bar dataKey="taps" fill="var(--color-taps)" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
    </div>
  );
}
