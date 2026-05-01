"use client";

import { useMutation } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface AddCampaignStepPayload {
  campaignId: string;
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
 * POST /api/v1/campaigns/{campaignId}/steps/
 *
 * Nota: campaignId va EN EL PAYLOAD del mutate (no en el constructor del hook).
 * Razón: si el caller crea el hook antes de tener el campaignId real (e.g. en flujos
 * "create campaign → add step" secuenciales), el closure del mutationFn capturaría
 * un valor stale. Pasarlo per-call lo evita.
 */
export function useAddCampaignStepMutation() {
  return useMutation<CampaignStepResponse, Error, AddCampaignStepPayload>({
    mutationFn: async ({ campaignId, ...body }) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/steps/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errBody = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(errBody.detail ?? `Error al agregar paso: ${res.status}`);
      }
      return res.json() as Promise<CampaignStepResponse>;
    },
  });
}
