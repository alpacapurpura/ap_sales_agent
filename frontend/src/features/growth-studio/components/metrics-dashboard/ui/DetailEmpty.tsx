'use client';

import { BarChart3 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { StageSummary } from '../../../types/metrics';

interface DetailEmptyProps {
  /** Stage context used to tailor the CTA copy */
  stage: StageSummary;
}

const STAGE_CTA_MAP: Record<string, string> = {
  ATRACCION: 'configuracion de canales de trafico',
  CAPTURA: 'configuracion de landing pages y formularios',
  NUTRICION: 'automatizaciones y campanas de retargeting',
  OPORTUNIDAD: 'configuracion de checkout y calificacion de leads',
  VENTAS: 'Offer Ladder y metodos de pago',
  ADOPCION: 'seguimiento de activacion de clientes',
  EXPANSION: 'ofertas de renovacion y upsell',
  EVANGELIZACION: 'programa de referidos y encuestas NPS',
};

/**
 * Empty state for a detail panel when the period has no data available.
 *
 * Renders a centered icon + heading + contextual body copy based on the
 * stage name. Uses muted/secondary tones per the UI-SPEC color system.
 */
export default function DetailEmpty({ stage }: DetailEmptyProps) {
  const ctaContext = STAGE_CTA_MAP[stage.id] ?? 'configuracion del embudo';

  return (
    <Card className="border-dashed border-muted-foreground/25">
      <CardContent className="flex flex-col items-center justify-center gap-4 py-12 px-6 text-center">
        {/* Muted illustration icon */}
        <div className="rounded-full bg-muted p-4">
          <BarChart3 className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">
            Sin datos para este periodo
          </h3>
          <p className="text-xs text-muted-foreground max-w-xs">
            Los datos apareceran aqui cuando el periodo tenga metricas disponibles.
            Verifica la {ctaContext}.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
