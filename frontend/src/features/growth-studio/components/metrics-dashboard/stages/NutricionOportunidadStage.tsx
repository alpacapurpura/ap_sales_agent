'use client';

import { NurtureOpportunityDetail } from '../detail-panels/NurtureOpportunityDetail';
import { useGrowthStudioContext } from '../context/GrowthStudioContext';

export function NutricionOportunidadStage() {
  const { handleMetricClick, handleConfigure, handleDisconnectedClick, handleNoDataClick } = useGrowthStudioContext();
  return (
    <NurtureOpportunityDetail
      onMetricClick={handleMetricClick}
      onConfigure={handleConfigure}
      onDisconnectedClick={handleDisconnectedClick}
      onNoDataClick={handleNoDataClick}
    />
  );
}
