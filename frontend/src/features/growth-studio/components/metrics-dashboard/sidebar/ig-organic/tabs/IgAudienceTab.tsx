'use client';

import { Loader2 } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip } from 'recharts';

import { ChartContainer } from '@/components/ui/chart';
import type { ChannelDashboardData } from '../../../../../types/metrics';
import { ChartInfoTooltip } from '../ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';

interface IgAudienceTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function IgAudienceTab({ data, isLoading }: IgAudienceTabProps) {
  if (isLoading) return <div className="flex items-center justify-center py-24"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>;
  if (!data) return <div className="py-24 text-center text-sm text-muted-foreground">No hay datos disponibles</div>;

  const followsSeries = data.timeSeries.find(ts => ts.metricName === 'ig_follows_and_unfollows');
  const followsData = followsSeries?.dataPoints.map(p => ({ date: p.date.slice(5), follows: p.value })) ?? [];

  return (
    <div className="space-y-8">
      {followsData.length > 0 && (
        <ChartSection slug="seguidores-netos">
          <div className="space-y-2">
            <ChartInfoTooltip title="Seguidores Netos por Día" description="Diferencia entre follows y unfollows diarios." />
            <ChartContainer config={{ follows: { label: 'Seguidores netos', color: 'hsl(var(--chart-1))' } }} className="h-[250px] w-full">
              <BarChart data={followsData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" className="text-xs" />
                <YAxis className="text-xs" />
                <RechartsTooltip />
                <Bar dataKey="follows" fill="var(--color-follows)" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </div>
        </ChartSection>
      )}
      <ChartSection slug="demografia">
        <div className="space-y-2">
          <ChartInfoTooltip title="Demografía de la Audiencia" description="Distribución por edad, género y ubicación de tus seguidores." />
          <div className="rounded-lg border bg-muted/30 p-6 text-center">
            <p className="text-sm text-muted-foreground">Datos demográficos disponibles próximamente</p>
            <p className="text-xs text-muted-foreground mt-1">Edad, género y ubicación de seguidores y cuentas engaged</p>
          </div>
        </div>
      </ChartSection>
    </div>
  );
}
