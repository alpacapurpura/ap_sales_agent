"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { updateTenantProfile } from "../api/tenant-profile-api";

import { TENANT_PROFILE_QUERY_KEY } from "./use-tenant-profile";

import type { RateLimitedError, UpdateTenantProfileRequest } from "../types/tenant-profile";

/** Successful mutation returns the updated TenantProfileResponse. */
interface UpdateSuccess {
  ok: true;
  data: unknown;
}

/** 409 rate-limit error shape from CONTRACT §3.3. */
interface UpdateRateLimited {
  ok: false;
  error: RateLimitedError;
}

export type UpdateTenantProfileResult = UpdateSuccess | UpdateRateLimited;

/**
 * React Query mutation to update the tenant's business_types.
 *
 * On success: invalidates ['tenant-profile'], ['offer-type-presets'],
 * ['offer-formats'] so all dependent UI re-fetches.
 *
 * On 409 (rate-limited): returns a typed error shape instead of throwing,
 * so callers can display the next_allowed_change_at date.
 *
 * CONTRACT §6.5
 */
export function useUpdateTenantProfile() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation<UpdateTenantProfileResult, Error, UpdateTenantProfileRequest>({
    mutationFn: async (payload: UpdateTenantProfileRequest): Promise<UpdateTenantProfileResult> => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");

      const res = await updateTenantProfile(token, payload);

      if (res.status === 409) {
        const body = (await res.json()) as { next_allowed_change_at?: string };
        const rateLimitError: RateLimitedError = {
          code: "rate_limited",
          next_allowed_change_at: body.next_allowed_change_at ?? new Date().toISOString(),
        };
        return { ok: false, error: rateLimitError };
      }

      if (!res.ok) {
        throw new Error(`Error al actualizar perfil: ${res.status} ${res.statusText}`);
      }

      const data: unknown = await res.json();
      return { ok: true, data };
    },
    onSuccess: (result) => {
      if (!result.ok) return;
      void queryClient.invalidateQueries({ queryKey: TENANT_PROFILE_QUERY_KEY });
      void queryClient.invalidateQueries({ queryKey: ["offer-type-presets"] });
      void queryClient.invalidateQueries({ queryKey: ["offer-formats"] });
    },
  });
}
