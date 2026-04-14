"use client";

import { BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { StageSummary } from "../../../types/metrics";

interface DetailEmptyProps {
  /** Stage context used to tailor the CTA copy */
  stage: StageSummary;
}

const STAGE_CTA_MAP: Record<string, string> = {
  ATRACCION: "configuración de canales de tráfico",
  CAPTURA: "configuración de landing pages y formularios",
  NUTRICION: "automatizaciones y campañas de retargeting",
  OPORTUNIDAD: "configuración de checkout y calificación de leads",
  VENTAS: "Offer Ladder y métodos de pago",
  ADOPCION: "seguimiento de activación de clientes",
  EXPANSION: "ofertas de renovación y upsell",
  EVANGELIZACION: "programa de referidos y encuestas NPS",
};

/**
 * Empty state for a detail panel when the period has no data available.
 *
 * Renders a centered icon + heading + contextual body copy based on the
 * stage name. Uses muted/secondary tones per the UI-SPEC color system.
 */
export default function DetailEmpty({ stage }: DetailEmptyProps) {
  const ctaContext = STAGE_CTA_MAP[stage.id] ?? "configuración del embudo";

  return (
    <Card className="border-dashed border-muted-foreground/25">
      <CardContent className="flex flex-col items-center justify-center gap-4 py-12 px-6 text-center">
        {/* Muted illustration icon */}
        <div className="rounded-full bg-muted p-4">
          <BarChart3 className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-foreground">Sin datos para este período</h3>
          <p className="text-xs text-muted-foreground max-w-xs">
            Los datos aparecerán aquí cuando el período tenga métricas disponibles. Verifica la{" "}
            {ctaContext}.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
