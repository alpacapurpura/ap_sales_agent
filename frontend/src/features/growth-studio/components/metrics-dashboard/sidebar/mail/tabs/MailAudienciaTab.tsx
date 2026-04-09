'use client';

import { Users } from 'lucide-react';
import type { MetaAdsPeriod } from '../../../../../types/metrics';

interface MailAudienciaTabProps {
  period: MetaAdsPeriod;
}

export function MailAudienciaTab({ period }: MailAudienciaTabProps) {
  void period;
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
        <Users className="h-8 w-8 text-amber-500" />
      </div>
      <div className="text-center">
        <h3 className="text-lg font-semibold">Audiencia</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Próximamente: segmentación por engagement, fuentes de suscripción y heatmap de actividad.
        </p>
      </div>
    </div>
  );
}
