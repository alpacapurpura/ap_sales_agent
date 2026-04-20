"use client";

import { useGrowthStudioContext } from "../context/GrowthStudioContext";
import { AdoptionDetail } from "../detail-panels/AdoptionDetail";

/**
 *
 */
export function AdopcionStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <AdoptionDetail onMetricClick={handleMetricClick} />;
}
