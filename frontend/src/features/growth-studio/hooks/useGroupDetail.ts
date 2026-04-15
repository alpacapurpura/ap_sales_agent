"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { stageOverviewApi } from "../api/stage-overview-api";
import { useGrowthStudioContext } from "../components/metrics-dashboard/context/GrowthStudioContext";

import type { TrafficGroup } from "../types/metrics";

interface GroupDetailData {
  channels: TrafficGroup["channels"];
  totals: TrafficGroup["totals"];
}

interface UseGroupDetailOptions {
  /** When false, the query will not execute. Defaults to false (load on demand). */
  enabled?: boolean;
}

/**
 * Fetches detail data for a specific group within a stage (Tier 2).
 *
 * Calls the dedicated group detail endpoint: GET /metrics/{stage}/groups/{groupKey}
 * Loads ONLY when `enabled=true` — intended to be triggered by IntersectionObserver
 * when the group enters the viewport.
 */
export function useGroupDetail(stage: string, groupKey: string, options?: UseGroupDetailOptions) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;
  const { selectedPeriod } = useGrowthStudioContext();

  return useQuery<GroupDetailData | undefined>({
    queryKey: ["stage-group-detail", tenantId, stage, groupKey, selectedPeriod],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");

      const result = await stageOverviewApi.getGroupDetail(token, stage, groupKey, selectedPeriod);
      return {
        channels: result.channels,
        totals: result.totals,
      };
    },
    staleTime: 1000 * 60 * 5,
    enabled: options?.enabled ?? false,
  });
}
