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

const mockGetStageOverview = vi.fn().mockResolvedValue({
  stage: "attraction",
  headerKpis: { reach: 15000, sessions: 3000 },
  miniFunnel: null,
  groups: [
    { groupKey: "paid", groupLabel: "Paid", channelCount: 2 },
    { groupKey: "organic_social", groupLabel: "Orgánico", channelCount: 3 },
  ],
  channelList: [
    {
      slug: "meta-ads",
      name: "Meta Ads",
      channelType: "paid",
      groupKey: "paid",
      connected: true,
      headlineKpi: { name: "spend", value: 1500, unit: "currency" },
      stale: false,
    },
    {
      slug: "ig-organic",
      name: "Instagram",
      channelType: "organic_social",
      groupKey: "organic_social",
      connected: true,
      headlineKpi: { name: "reach", value: 8000 },
      stale: false,
    },
  ],
  bottlenecks: [],
  period: "last_30_days",
});

vi.mock("../../api/stage-overview-api", () => ({
  stageOverviewApi: {
    getStageOverview: (...args: unknown[]) => mockGetStageOverview(...args),
  },
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { GrowthStudioProvider } from "../../components/metrics-dashboard/context/GrowthStudioContext";
import { useStageOverview } from "../use-stage-overview";

// ── Tests ──────────────────────────────────────────────────────────────────────

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

describe("useStageOverview", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    if (typeof window !== "undefined") {
      window.localStorage.setItem("x-tenant-id", "test-tenant");
    }
  });

  it("fetches overview data for a stage", async () => {
    const { result } = renderHook(() => useStageOverview("attraction"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.stage).toBe("attraction");
    expect(result.current.data?.channelList).toHaveLength(2);
  });

  it("returns channel list with groupKey per channel", async () => {
    const { result } = renderHook(() => useStageOverview("attraction"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    const metaAds = result.current.data?.channelList.find((c) => c.slug === "meta-ads");
    expect(metaAds?.groupKey).toBe("paid");
    expect(metaAds?.headlineKpi?.name).toBe("spend");
  });

  it("includes groups metadata", async () => {
    const { result } = renderHook(() => useStageOverview("attraction"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.groups).toHaveLength(2);
    expect(result.current.data?.groups[0].groupKey).toBe("paid");
  });

  it("does not fetch when disabled", async () => {
    renderHook(() => useStageOverview("attraction", { enabled: false }), {
      wrapper: createWrapper(),
    });

    // Wait a tick for any potential calls
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(mockGetStageOverview).not.toHaveBeenCalled();
  });
});
