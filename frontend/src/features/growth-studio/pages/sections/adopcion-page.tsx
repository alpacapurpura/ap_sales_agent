"use client";

import { AdopcionStage } from "@/features/growth-studio/components/metrics-dashboard/stages/AdopcionStage";

/**
 * Página de sección para la etapa Adopción.
 *
 * Wrapper delgado que delega al componente de Stage existente.
 * Importado por StageDispatcher vía next/dynamic (lazy-loading).
 */
export function AdopcionPage() {
  return <AdopcionStage />;
}
