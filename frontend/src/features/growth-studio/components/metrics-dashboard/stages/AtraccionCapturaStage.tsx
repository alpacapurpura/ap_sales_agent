"use client";

import { useGrowthStudioContext } from "../context/GrowthStudioContext";
import { AttractionCaptureDetail } from "../detail-panels/AttractionCaptureDetail";

export function AtraccionCapturaStage() {
  const {
    handleMetricClick,
    handleConfigure,
    handleChannelClick,
    handleDisconnectedClick,
    handleNoDataClick,
  } = useGrowthStudioContext();
  return (
    <AttractionCaptureDetail
      onMetricClick={handleMetricClick}
      onConfigure={handleConfigure}
      onChannelClick={handleChannelClick}
      onDisconnectedClick={handleDisconnectedClick}
      onNoDataClick={handleNoDataClick}
    />
  );
}
