"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface CreateSegmentPayload {
  name: string;
  description?: string;
  segment_type: "STATIC";
  lead_ids: string[];
}

export interface SegmentResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  segment_type: string;
  created_at: string;
  updated_at: string | null;
}

/**
 * Mutation para crear un segmento STATIC con lead_ids snapshot.
 * POST /api/v1/segments/
 * fetchClient auto-inyecta X-Tenant-ID.
 */
export function useCreateSegmentMutation() {
  const queryClient = useQueryClient();

  return useMutation<SegmentResponse, Error, CreateSegmentPayload>({
    mutationFn: async (payload) => {
      const res = await fetchClient(`${API_URL}/api/v1/segments/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(body.detail ?? `Error al crear segmento: ${res.status}`);
      }
      return res.json() as Promise<SegmentResponse>;
    },
    onSuccess: () => {
      // Invalidar lista de segmentos para refrescar cualquier lista futura
      void queryClient.invalidateQueries({ queryKey: ["crm", "segments"] });
    },
  });
}
