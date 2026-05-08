"use client";

import { AtraccionCapturaStage } from "@/features/growth-studio/components/metrics-dashboard/stages/AtraccionCapturaStage";

/**
 * Página de sección para la etapa Atracción y Captura.
 *
 * Wrapper delgado que delega al componente de Stage existente.
 * El Stage component consume el contexto de GrowthStudioProvider
 * (provisto por el layout de growth-studio).
 *
 * Importado por StageDispatcher vía next/dynamic (lazy-loading).
 */
export function AtraccionCapturaPage() {
  return <AtraccionCapturaStage />;
}
