"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ScheduleCampaignPayload {
  scheduled_for: string; // ISO 8601
}

/**
 * Mutation para programar una campaña.
 * POST /api/v1/campaigns/{id}/schedule
 */
export function useScheduleCampaignMutation(campaignId: string) {
  const queryClient = useQueryClient();

  return useMutation<CampaignResponse, Error, ScheduleCampaignPayload>({
    mutationFn: async (payload) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail ?? `Error al programar campaña: ${res.status}`);
      }
      return res.json() as Promise<CampaignResponse>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["campaigns", campaignId] });
    },
  });
}
