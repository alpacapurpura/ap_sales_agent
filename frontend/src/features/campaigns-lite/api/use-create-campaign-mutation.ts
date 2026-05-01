"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface CreateCampaignPayload {
  name: string;
  description?: string;
  campaign_type: string;
  segment_id: string;
  channel_priority: string[];
  created_by_source?: string;
}

/**
 * Mutation para crear una campaña.
 * POST /api/v1/campaigns/
 */
export function useCreateCampaignMutation() {
  const queryClient = useQueryClient();

  return useMutation<CampaignResponse, Error, CreateCampaignPayload>({
    mutationFn: async (payload) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail ?? `Error al crear campaña: ${res.status}`);
      }
      return res.json() as Promise<CampaignResponse>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });
}
