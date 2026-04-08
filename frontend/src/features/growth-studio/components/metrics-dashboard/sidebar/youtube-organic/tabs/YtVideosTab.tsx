'use client';

import { Loader2 } from 'lucide-react';

import type { ChannelDashboardData } from '../../../../../types/metrics';
import { YouTubeTopVideosList } from '../../youtube/YouTubeTopVideosList';
import { YouTubeTrafficSourcesChart } from '../../youtube/YouTubeTrafficSourcesChart';
import { ChartInfoTooltip } from '../../ig-organic/ChartInfoTooltip';
import { ChartSection } from '../../shared/ChartSection';

interface YtVideosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function YtVideosTab({ data, isLoading }: YtVideosTabProps) {
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

  return (
    <div className="space-y-8">
      <ChartSection slug="top-videos">
        <div className="space-y-3">
          <ChartInfoTooltip
            title="Top Videos"
            description="Videos con mejor rendimiento en el periodo seleccionado. Ordenados por vistas. Los videos de 60s o menos se clasifican como Shorts."
          />
          <YouTubeTopVideosList enabled />
        </div>
      </ChartSection>

      <ChartSection slug="fuentes-trafico">
        <div className="space-y-3">
          <ChartInfoTooltip
            title="Fuentes de Tr&aacute;fico"
            description="De d&oacute;nde vienen tus vistas. 'Recomendaciones YT' = el algoritmo te est&aacute; promoviendo. 'B&uacute;squeda YT' = tu SEO funciona."
          />
          <YouTubeTrafficSourcesChart enabled />
        </div>
      </ChartSection>
    </div>
  );
}
