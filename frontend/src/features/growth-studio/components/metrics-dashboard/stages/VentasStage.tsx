"use client";

import { useGrowthStudioContext } from "../context/GrowthStudioContext";
import { SalesDetail } from "../detail-panels/SalesDetail";

export function VentasStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <SalesDetail onMetricClick={handleMetricClick} />;
}
