"use client";

import { ExpansionEvangelizacionStage } from "@/features/growth-studio/components/metrics-dashboard/stages/ExpansionEvangelizacionStage";

/**
 * Página de sección para la etapa Expansión y Evangelización.
 *
 * Wrapper delgado que delega al componente de Stage existente.
 * Importado por StageDispatcher vía next/dynamic (lazy-loading).
 */
export function ExpansionEvangelizacionPage() {
  return <ExpansionEvangelizacionStage />;
}
