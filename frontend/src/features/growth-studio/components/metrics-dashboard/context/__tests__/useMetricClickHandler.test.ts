import { renderHook, act } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { useMetricClickHandler } from "../useMetricClickHandler";

import type { MetricClickData } from "../../../../types/metrics";

describe("useMetricClickHandler", () => {
  const mockMetric: MetricClickData = {
    stageId: "ATRACCION",
    channelSlug: "meta-ads",
    metricName: "impressions",
    currentValue: 1000,
  };

  it("starts with sidebar closed and no metric", () => {
    const { result } = renderHook(() => useMetricClickHandler());
    expect(result.current.sidebarOpen).toBe(false);
    expect(result.current.sidebarMetric).toBeNull();
  });

  it("opens sidebar with metric on handleMetricClick", () => {
    const { result } = renderHook(() => useMetricClickHandler());
    act(() => result.current.handleMetricClick(mockMetric));
    expect(result.current.sidebarOpen).toBe(true);
    expect(result.current.sidebarMetric).toEqual(mockMetric);
  });

  it("closes sidebar and clears metric on handleSidebarClose", () => {
    const { result } = renderHook(() => useMetricClickHandler());
    act(() => result.current.handleMetricClick(mockMetric));
    act(() => result.current.handleSidebarClose());
    expect(result.current.sidebarOpen).toBe(false);
    expect(result.current.sidebarMetric).toBeNull();
  });

  it("exposes setSidebarOpen for external control", () => {
    const { result } = renderHook(() => useMetricClickHandler());
    act(() => result.current.setSidebarOpen(true));
    expect(result.current.sidebarOpen).toBe(true);
  });
});
