"use client";

import { useAuth } from "@clerk/nextjs";
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
 * Mutation to create a STATIC segment with a lead_ids snapshot.
 * POST /api/v1/segments/.
 *
 * Auth pattern (homologated with offer-studio/use-assets.ts): the
 * mutation throws "No autenticado" if Clerk hasn't issued a JWT yet,
 * so we never send the literal "Bearer null" that would 401 → kick
 * the user out to /sign-in via fetchClient's redirect handler.
 *
 * fetchClient auto-injects X-Tenant-ID.
 */
export function useCreateSegmentMutation() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<SegmentResponse, Error, CreateSegmentPayload>({
    mutationFn: async (payload) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      const res = await fetchClient(`${API_URL}/api/v1/segments/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
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
