"use client";

import { VentasStage } from "@/features/growth-studio/components/metrics-dashboard/stages/VentasStage";

/**
 * Página de sección para la etapa Ventas.
 *
 * Wrapper delgado que delega al componente de Stage existente.
 * Importado por StageDispatcher vía next/dynamic (lazy-loading).
 */
export function VentasPage() {
  return <VentasStage />;
}
