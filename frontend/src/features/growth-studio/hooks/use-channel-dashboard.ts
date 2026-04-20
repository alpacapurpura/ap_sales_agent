"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchChannelDashboard } from "../api/channel-dashboard-api";

import type { ChannelDashboardData, MetaAdsPeriod } from "../types/metrics";

/**
 *
 */
export function useChannelDashboard(
  channelSlug: string,
  period: MetaAdsPeriod = "30d",
  enabled = true,
) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<ChannelDashboardData>({
    queryKey: ["channel-dashboard", tenantId, channelSlug, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchChannelDashboard(token, channelSlug, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}
