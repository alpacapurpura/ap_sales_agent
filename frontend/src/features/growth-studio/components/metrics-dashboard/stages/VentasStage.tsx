"use client";

import { SalesDetail } from "../detail-panels/SalesDetail";
import { useGrowthStudioContext } from "../context/GrowthStudioContext";

export function VentasStage() {
  const { handleMetricClick } = useGrowthStudioContext();
  return <SalesDetail onMetricClick={handleMetricClick} />;
}
