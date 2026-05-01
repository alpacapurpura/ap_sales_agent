"use client";

import { useMutation } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface AddCampaignStepPayload {
  step_type: string;
  step_index: number;
  step_config: Record<string, unknown>;
}

export interface CampaignStepResponse {
  id: string;
  campaign_id: string;
  step_type: string;
  step_index: number;
  step_config: Record<string, unknown>;
  created_at: string;
}

/**
 * Mutation para agregar un paso a una campaña.
 * POST /api/v1/campaigns/{id}/steps/
 */
export function useAddCampaignStepMutation(campaignId: string) {
  return useMutation<CampaignStepResponse, Error, AddCampaignStepPayload>({
    mutationFn: async (payload) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/steps/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail ?? `Error al agregar paso: ${res.status}`);
      }
      return res.json() as Promise<CampaignStepResponse>;
    },
  });
}
