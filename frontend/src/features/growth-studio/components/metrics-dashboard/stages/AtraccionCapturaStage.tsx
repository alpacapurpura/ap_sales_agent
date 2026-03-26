'use client';

import { AttractionCaptureDetail } from '../detail-panels/AttractionCaptureDetail';
import { useGrowthStudioContext } from '../context/GrowthStudioContext';

export function AtraccionCapturaStage() {
  const { handleMetricClick, handleConfigure } = useGrowthStudioContext();
  return <AttractionCaptureDetail onMetricClick={handleMetricClick} onConfigure={handleConfigure} />;
}
