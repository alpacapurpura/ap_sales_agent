"use client";

import { ExpansionEvangelizationDetail } from "../detail-panels/ExpansionEvangelizationDetail";
import { useGrowthStudioContext } from "../context/GrowthStudioContext";

export function ExpansionEvangelizacionStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <ExpansionEvangelizationDetail onMetricClick={handleMetricClick} />;
}
