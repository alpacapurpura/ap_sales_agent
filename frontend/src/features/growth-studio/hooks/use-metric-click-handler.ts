import { useState, useCallback } from "react";

import type { MetricClickData } from "../types/metrics";

/**
 * Encapsulates metric sidebar open/close state.
 * Extracted from GrowthStudioContext to isolate this concern.
 */
export function useMetricClickHandler() {
  const [sidebarMetric, setSidebarMetric] = useState<MetricClickData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleMetricClick = useCallback((metric: MetricClickData) => {
    setSidebarMetric(metric);
    setSidebarOpen(true);
  }, []);

  const handleSidebarClose = useCallback(() => {
    setSidebarOpen(false);
    setSidebarMetric(null);
  }, []);

  return {
    sidebarMetric,
    sidebarOpen,
    setSidebarOpen,
    setSidebarMetric,
    handleMetricClick,
    handleSidebarClose,
  };
}
