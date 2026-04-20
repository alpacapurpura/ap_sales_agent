import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchBowtiesSummary } from "../api/summary-api";

import type { BowtiesSummary } from "../types/summary";

/**
 *
 */
export function useBowtiesSummary() {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<BowtiesSummary>({
    queryKey: ["bowties-summary", tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchBowtiesSummary(token);
    },
    staleTime: 1000 * 60 * 1, // 1 min — shorter than detail hooks for Bowtie freshness
    gcTime: 1000 * 60 * 5, // 5 min — keep cached between stage navigations
    refetchOnWindowFocus: false,
  });
}
