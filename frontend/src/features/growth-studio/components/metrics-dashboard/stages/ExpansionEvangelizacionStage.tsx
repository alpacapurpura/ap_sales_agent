"use client";

import { useGrowthStudioContext } from "../context/GrowthStudioContext";
import { ExpansionEvangelizationDetail } from "../detail-panels/ExpansionEvangelizationDetail";

export function ExpansionEvangelizacionStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <ExpansionEvangelizationDetail onMetricClick={handleMetricClick} />;
}
