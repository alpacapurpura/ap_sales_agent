'use client';

import { Loader2, Users } from 'lucide-react';

import { useDemographics } from '../../../../../api/campaigns-api';
import type { ChannelDashboardData, MetaAdsPeriod } from '../../../../../types/metrics';
import { ReachFrequencySection } from '../ReachFrequencySection';

interface AudienciaTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
  period?: MetaAdsPeriod;
}

export function AudienciaTab({ data, isLoading, period }: AudienciaTabProps) {
  const { data: demographics } = useDemographics('meta-ads', period ?? '30d');

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
      {/* Reach + Frequency */}
      <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />

      {/* Demographic Breakdown */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Demograf&iacute;a de tu audiencia
        </h3>
        <div className="grid grid-cols-3 gap-4">
          {/* Age Distribution */}
          {demographics?.age && demographics.age.length > 0 ? (
            <div className="rounded-lg border bg-card p-4">
              <h4
                className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
                title="Distribuci&oacute;n de edad de las personas que ven tus anuncios."
              >
                Distribuci&oacute;n por edad
              </h4>
              <div className="space-y-2">
                {demographics.age.map(seg => (
                  <div key={seg.label} className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground w-10 text-right">{seg.label}</span>
                    <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                      <div
                        className="bg-blue-500/50 h-full rounded-full flex items-center pl-2 text-[9px] font-medium"
                        style={{ width: `${Math.max(seg.percentage, 5)}%` }}
                      >
                        {seg.percentage.toFixed(0)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
              <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
              <p className="font-medium text-xs">Distribuci&oacute;n por edad</p>
              <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; desglose 18-24, 25-34, 35-44, 45-54, 55+</p>
            </div>
          )}

          {/* Gender Distribution */}
          {demographics?.gender && demographics.gender.length > 0 ? (
            <div className="rounded-lg border bg-card p-4">
              <h4
                className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
                title="Proporci&oacute;n femenino vs masculino de tu audiencia."
              >
                Distribuci&oacute;n por g&eacute;nero
              </h4>
              <div className="flex items-center justify-around py-2">
                {demographics.gender.map(seg => (
                  <div key={seg.label} className="text-center">
                    <p className="text-2xl font-bold tabular-nums">{seg.percentage.toFixed(0)}%</p>
                    <p className="text-[11px] text-muted-foreground mt-1">{seg.label}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
              <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
              <p className="font-medium text-xs">Distribuci&oacute;n por g&eacute;nero</p>
              <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; femenino vs masculino</p>
            </div>
          )}

          {/* Placement Distribution */}
          {demographics?.placement && demographics.placement.length > 0 ? (
            <div className="rounded-lg border bg-card p-4">
              <h4
                className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3"
                title="D&oacute;nde aparecen tus anuncios (Feed, Stories, Reels, etc.)."
              >
                D&oacute;nde aparecen tus ads
              </h4>
              <div className="space-y-2">
                {demographics.placement.map(seg => (
                  <div key={seg.label} className="flex items-center gap-2">
                    <span className="text-[11px] text-muted-foreground w-14 text-right truncate" title={seg.label}>
                      {seg.label}
                    </span>
                    <div className="flex-1 rounded-full bg-muted h-5 overflow-hidden">
                      <div
                        className="bg-violet-500/50 h-full rounded-full flex items-center pl-2 text-[9px] font-medium"
                        style={{ width: `${Math.max(seg.percentage, 5)}%` }}
                      >
                        {seg.percentage.toFixed(0)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
              <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
              <p className="font-medium text-xs">D&oacute;nde aparecen tus ads</p>
              <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; Feed, Stories, Reels, Otros</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
