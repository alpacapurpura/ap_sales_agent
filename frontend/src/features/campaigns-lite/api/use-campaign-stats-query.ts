"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignStatsResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Fetches stats for a campaign.
 * GET /api/v1/campaigns/{id}/stats
 */
export function useCampaignStatsQuery(campaignId: string | null) {
  return useQuery<CampaignStatsResponse, Error>({
    queryKey: ["campaigns", campaignId, "stats"],
    queryFn: async () => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/stats`);
      if (!res.ok) throw new Error(`Error al cargar estadísticas: ${res.status}`);
      return res.json() as Promise<CampaignStatsResponse>;
    },
    enabled: !!campaignId,
    staleTime: 30_000,
  });
}
