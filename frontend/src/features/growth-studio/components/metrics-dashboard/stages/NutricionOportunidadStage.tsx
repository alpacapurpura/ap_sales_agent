"use client";

import { NurtureOpportunityDetail } from "../detail-panels/NurtureOpportunityDetail";
import { useGrowthStudioContext } from "../context/GrowthStudioContext";

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
