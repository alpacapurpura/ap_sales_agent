'use client';

import { Film, ImageIcon, LayoutGrid, Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';
import { useCreativesOverview } from '../../../../../api/campaigns-api';
import type { ChannelDashboardData, MetaAdsPeriod } from '../../../../../types/metrics';

interface CreativosTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

export function CreativosTab({ data, isLoading, period }: CreativosTabProps) {
  const { data: creatives } = useCreativesOverview(period ?? '30d');

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
      {/* Top Performing Ads */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Top anuncios por rendimiento
        </h3>
        {creatives?.ads && creatives.ads.length > 0 ? (
          <div className="grid grid-cols-3 gap-3">
            {creatives.ads.slice(0, 6).map(ad => (
              <div key={ad.externalId} className="rounded-xl border bg-card p-3 space-y-2">
                {ad.creativeThumbnailUrl ? (
                  /* eslint-disable-next-line @next/next/no-img-element */
                  <img
                    src={ad.creativeThumbnailUrl}
                    alt={ad.name}
                    className="h-28 w-full rounded-lg object-cover"
                  />
                ) : (
                  <div className="h-28 rounded-lg bg-muted flex items-center justify-center text-xs text-muted-foreground">
                    Sin preview
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium truncate">{ad.name}</p>
                  <p className="text-[10px] text-muted-foreground truncate">
                    {ad.campaignName ?? 'Sin campa\u00f1a'}
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <span
                    className={cn(
                      'rounded-full px-2 py-0.5 text-[9px]',
                      ad.effectiveStatus === 'ACTIVE'
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : ad.effectiveStatus === 'PAUSED'
                          ? 'bg-zinc-500/10 text-zinc-400'
                          : 'bg-amber-500/10 text-amber-500',
                    )}
                  >
                    {ad.effectiveStatus === 'ACTIVE'
                      ? 'Activo'
                      : ad.effectiveStatus === 'PAUSED'
                        ? 'Pausado'
                        : ad.effectiveStatus}
                  </span>
                  {ad.creativeCta && (
                    <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[9px] text-blue-400">
                      {ad.creativeCta}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
            <Film className="h-8 w-8 mx-auto mb-2 opacity-40" />
            <p className="font-medium">Pr&oacute;ximamente</p>
            <p className="mt-1 text-xs">
              Ranking de tus mejores y peores anuncios con thumbnails, ROAS y CPA por creativo.
            </p>
          </div>
        )}
      </div>

      {/* Format Comparison + Video Retention */}
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

        {/* Video Retention */}
        <div>
          <h3
            className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
            title="Cu&aacute;ntas personas ven tu video hasta cada punto. Ideal: >30% completa el video."
          >
            Retenci&oacute;n de video
          </h3>
          {creatives?.videoRetention && creatives.videoRetention.plays > 0 ? (
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-end gap-2 h-[180px] px-2">
                {[
                  { label: 'Play', value: creatives.videoRetention.plays, pct: 100 },
                  {
                    label: '25%',
                    value: creatives.videoRetention.p25,
                    pct: (creatives.videoRetention.p25 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '50%',
                    value: creatives.videoRetention.p50,
                    pct: (creatives.videoRetention.p50 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '75%',
                    value: creatives.videoRetention.p75,
                    pct: (creatives.videoRetention.p75 / creatives.videoRetention.plays) * 100,
                  },
                  {
                    label: '100%',
                    value: creatives.videoRetention.p100,
                    pct: (creatives.videoRetention.p100 / creatives.videoRetention.plays) * 100,
                  },
                ].map((step, i) => (
                  <div key={step.label} className="flex-1 flex flex-col items-center gap-1">
                    <p className="text-[10px] font-semibold tabular-nums">
                      {step.value >= 1000 ? `${(step.value / 1000).toFixed(1)}k` : step.value.toFixed(0)}
                    </p>
                    <div
                      className={cn(
                        'w-full rounded-t',
                        i === 4
                          ? 'bg-emerald-500/50'
                          : i >= 3
                            ? 'bg-amber-500/40'
                            : 'bg-blue-500/50',
                      )}
                      style={{ height: `${Math.max(step.pct * 1.6, 4)}px` }}
                    />
                    <p className="text-[9px] text-muted-foreground">{step.label}</p>
                    {i > 0 && <p className="text-[8px] text-blue-400">{step.pct.toFixed(0)}%</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-8 text-center text-sm text-muted-foreground">
              <p className="font-medium">Pr&oacute;ximamente</p>
              <p className="mt-1 text-xs">
                Gr&aacute;fico de retenci&oacute;n: Play &rarr; 25% &rarr; 50% &rarr; 75% &rarr; 100% completado.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
