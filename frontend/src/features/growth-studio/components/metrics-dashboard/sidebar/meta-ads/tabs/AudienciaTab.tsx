'use client';

import { Loader2, Users } from 'lucide-react';

import { ReachFrequencySection } from '../ReachFrequencySection';
import type { ChannelDashboardData } from '../../../../../types/metrics';

interface AudienciaTabProps {
  data: ChannelDashboardData | undefined;
  isLoading: boolean;
}

export function AudienciaTab({ data, isLoading }: AudienciaTabProps) {
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
      {/* Reach + Frequency — moved here from Overview/Costs */}
      <ReachFrequencySection kpis={data.kpis} frequencyAlert={data.frequencyAlert} />

      {/* Demographic Breakdown — placeholder until audience data endpoint exists */}
      <div>
        <h3 className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Demograf&iacute;a de tu audiencia
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">Distribuci&oacute;n por edad</p>
            <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; desglose 18-24, 25-34, 35-44, 45-54, 55+</p>
          </div>
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">Distribuci&oacute;n por g&eacute;nero</p>
            <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; femenino vs masculino</p>
          </div>
          <div className="rounded-lg border bg-card p-6 text-center text-sm text-muted-foreground">
            <Users className="h-6 w-6 mx-auto mb-2 opacity-40" />
            <p className="font-medium text-xs">D&oacute;nde aparecen tus ads</p>
            <p className="mt-1 text-[10px]">Pr&oacute;ximamente &mdash; Feed, Stories, Reels, Otros</p>
          </div>
        </div>
      </div>
    </div>
  );
}
