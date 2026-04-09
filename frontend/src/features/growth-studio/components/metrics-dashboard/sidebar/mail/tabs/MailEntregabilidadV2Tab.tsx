'use client';

import { ShieldCheck } from 'lucide-react';
import type { MetaAdsPeriod } from '../../../../../types/metrics';

interface MailEntregabilidadV2TabProps {
  period: MetaAdsPeriod;
}

export function MailEntregabilidadV2Tab({ period }: MailEntregabilidadV2TabProps) {
  void period;
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-500/10">
        <ShieldCheck className="h-8 w-8 text-amber-500" />
      </div>
      <div className="text-center">
        <h3 className="text-lg font-semibold">Entregabilidad</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Próximamente: health score, rebotes, spam reports y tendencia de salud.
        </p>
      </div>
    </div>
  );
}
