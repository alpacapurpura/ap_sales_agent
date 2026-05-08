"use client";

import { NutricionOportunidadStage } from "@/features/growth-studio/components/metrics-dashboard/stages/NutricionOportunidadStage";

/**
 * Página de sección para la etapa Nutrición y Oportunidad.
 *
 * Wrapper delgado que delega al componente de Stage existente.
 * Importado por StageDispatcher vía next/dynamic (lazy-loading).
 */
export function NutricionOportunidadPage() {
  return <NutricionOportunidadStage />;
}
