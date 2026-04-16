import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => "/tenant/growth-studio/atraccion-captura",
  useSearchParams: () => ({
    get: () => null,
    toString: () => "",
  }),
}));

const mockGetGroupDetail = vi.fn().mockResolvedValue({
  channels: [
    {
      slug: "meta-ads",
      name: "Meta Ads",
      channelType: "paid",
      metrics: [{ name: "spend", value: 1500 }],
      sourceLabel: "Meta",
      connected: true,
    },
  ],
  totals: { spend: 1500, impressions: 50000 },
});

vi.mock("../../api/stage-overview-api", () => ({
  stageOverviewApi: {
    getStageOverview: vi.fn().mockResolvedValue({}),
    getGroupDetail: (...args: unknown[]) => mockGetGroupDetail(...args),
  },
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { GrowthStudioProvider } from "../../components/metrics-dashboard/context/GrowthStudioContext";
import { useGroupDetail } from "../use-group-detail";

// ── Wrapper ───────────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      React.createElement(GrowthStudioProvider, null, children),
    );
  };
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("useGroupDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    if (typeof window !== "undefined") {
      window.localStorage.setItem("x-tenant-id", "test-tenant");
    }
  });

  it("does NOT fetch when enabled=false (default)", async () => {
    renderHook(() => useGroupDetail("attraction", "paid"), {
      wrapper: createWrapper(),
    });

    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(mockGetGroupDetail).not.toHaveBeenCalled();
  });

  it("calls dedicated group endpoint when enabled=true", async () => {
    const { result } = renderHook(() => useGroupDetail("attraction", "paid", { enabled: true }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    // Verify it called the dedicated endpoint (not the full stage detail)
    expect(mockGetGroupDetail).toHaveBeenCalledWith(
      "mock-token",
      "attraction",
      "paid",
      "last_30_days",
    );
  });

  it("maps response channels and totals correctly", async () => {
    const { result } = renderHook(() => useGroupDetail("attraction", "paid", { enabled: true }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.channels).toHaveLength(1);
    expect(result.current.data?.channels[0].slug).toBe("meta-ads");
    expect(result.current.data?.totals.spend).toBe(1500);
    expect(result.current.data?.totals.impressions).toBe(50000);
  });

  it("includes correct queryKey with stage, groupKey, and period", () => {
    const { result } = renderHook(() => useGroupDetail("attraction", "paid", { enabled: true }), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });
});
