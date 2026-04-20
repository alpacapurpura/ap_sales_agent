"use client";

import { useGrowthStudioContext } from "../context/GrowthStudioContext";
import { NurtureOpportunityDetail } from "../detail-panels/NurtureOpportunityDetail";

/**
 *
 */
export function NutricionOportunidadStage() {
  const {
    handleMetricClick,
    handleChannelClick,
    handleConfigure,
    handleDisconnectedClick,
    handleNoDataClick,
  } = useGrowthStudioContext();
  return (
    <NurtureOpportunityDetail
      onMetricClick={handleMetricClick}
      onChannelClick={handleChannelClick}
      onConfigure={handleConfigure}
      onDisconnectedClick={handleDisconnectedClick}
      onNoDataClick={handleNoDataClick}
    />
  );
}
