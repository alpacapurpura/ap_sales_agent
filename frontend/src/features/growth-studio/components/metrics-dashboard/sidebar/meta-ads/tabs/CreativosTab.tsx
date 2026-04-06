'use client';

import { Film, ImageIcon, LayoutGrid, Loader2 } from 'lucide-react';

import type { ChannelDashboardData } from '../../../../../types/metrics';

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function CreativosTab({ data, isLoading }: CreativosTabProps) {
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
    <div className="space-y-6">
      {/* Top Performing Ads — placeholder until ad-level metrics endpoint exists */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Top anuncios por rendimiento
        </h3>
        <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
          <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
          <p className="font-medium">Pr&oacute;ximamente</p>
          <p className="mt-1 text-xs">
            Ranking de tus mejores y peores anuncios con thumbnails, ROAS y CPA por creativo.
          </p>
        </div>
      </div>

      {/* Format Comparison — placeholder */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
            Rendimiento por formato
          </h3>
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Film className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Video</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos pr&oacute;ximamente</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <LayoutGrid className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Carrusel</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos pr&oacute;ximamente</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Imagen est&aacute;tica</span>
              </div>
              <span className="text-xs text-muted-foreground">Datos pr&oacute;ximamente</span>
            </div>
          </div>
        </div>

        {/* Video Retention — placeholder */}
        <div>
          <h3
            className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
            title="Cuántas personas ven tu video hasta cada punto. Ideal: >30% completa el video."
          >
            Retenci&oacute;n de video
          </h3>
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            <p className="font-medium">Pr&oacute;ximamente</p>
            <p className="mt-1 text-xs">
              Gr&aacute;fico de retenci&oacute;n: Play &rarr; 25% &rarr; 50% &rarr; 75% &rarr; 100% completado.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
