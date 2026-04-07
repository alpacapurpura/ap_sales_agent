'use client';

import { AttractionCaptureDetail } from '../detail-panels/AttractionCaptureDetail';
import { useGrowthStudioContext } from '../context/GrowthStudioContext';

export function AtraccionCapturaStage() {
  const { handleMetricClick, handleConfigure, handleChannelClick } = useGrowthStudioContext();
  return <AttractionCaptureDetail onMetricClick={handleMetricClick} onConfigure={handleConfigure} onChannelClick={handleChannelClick} />;
}
