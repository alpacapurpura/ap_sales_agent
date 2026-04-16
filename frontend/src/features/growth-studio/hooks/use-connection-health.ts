"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchConnectionHealth } from "../api/connection-health-api";

import type { ConnectionHealthData } from "../api/connection-health-api";

export type { ConnectionHealthData };

export function useConnectionHealth(channelSlug: string, enabled = true) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<ConnectionHealthData>({
    queryKey: ["connection-health", tenantId, channelSlug],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchConnectionHealth(token, channelSlug);
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}
