"use client";

import { AdoptionDetail } from "../detail-panels/AdoptionDetail";
import { useGrowthStudioContext } from "../context/GrowthStudioContext";

export function AdopcionStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <AdoptionDetail onMetricClick={handleMetricClick} />;
}
