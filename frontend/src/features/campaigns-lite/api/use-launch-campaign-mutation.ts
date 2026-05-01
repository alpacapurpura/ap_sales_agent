import { useMutation } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import type { CampaignResponse } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

interface LaunchCampaignParams {
  campaignId: string;
}

/**
 * POST /api/v1/campaigns/{id}/launch — transición SCHEDULED|DRAFT → RUNNING.
 */
export function useLaunchCampaignMutation() {
  return useMutation<CampaignResponse, Error, LaunchCampaignParams>({
    mutationFn: async ({ campaignId }) => {
      const res = await fetchClient(`${API_URL}/api/v1/campaigns/${campaignId}/launch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail ?? `Error al lanzar campaña: ${res.status}`);
      }
      return res.json() as Promise<CampaignResponse>;
    },
  });
}
