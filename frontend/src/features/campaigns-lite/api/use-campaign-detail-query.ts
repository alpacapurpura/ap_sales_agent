"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * Fetches detail for a single campaign.
 * GET /api/v1/campaigns/{id}
 */
export function useCampaignDetailQuery(campaignId: string | null) {
  return useQuery<CampaignResponse, Error>({
    queryKey: ["campaigns", campaignId],
    queryFn: async () => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}`);
      if (!res.ok) throw new Error(`Error al cargar campaña: ${res.status}`);
      return res.json() as Promise<CampaignResponse>;
    },
    enabled: !!campaignId,
    staleTime: 15_000,
  });
}
