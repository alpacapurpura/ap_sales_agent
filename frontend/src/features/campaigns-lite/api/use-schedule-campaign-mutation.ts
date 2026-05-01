"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface ScheduleCampaignPayload {
  campaignId: string;
  scheduled_for: string; // ISO 8601
}

/**
 * Mutation para programar una campaña.
 * POST /api/v1/campaigns/{campaignId}/schedule
 *
 * Nota: campaignId va en payload (no constructor) — mismo motivo que useAddCampaignStepMutation:
 * permite usar el hook en flujos donde el campaignId aún no existe al renderizar.
 */
export function useScheduleCampaignMutation() {
  const queryClient = useQueryClient();

  return useMutation<CampaignResponse, Error, ScheduleCampaignPayload>({
    mutationFn: async ({ campaignId, ...body }) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/schedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const errBody = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(errBody.detail ?? `Error al programar campaña: ${res.status}`);
      }
      return res.json() as Promise<CampaignResponse>;
    },
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["campaigns", variables.campaignId] });
    },
  });
}
