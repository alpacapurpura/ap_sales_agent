"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { getTenantProfile } from "../api/tenant-profile-api";

import type { TenantProfileResponse } from "../types/tenant-profile";

export const TENANT_PROFILE_QUERY_KEY = ["tenant-profile"] as const;

/**
 * React Query hook to fetch the current tenant profile.
 *
 * CONTRACT §6.1 — GET /api/v1/tenant/profile
 */
export function useTenantProfile() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<TenantProfileResponse>({
    queryKey: TENANT_PROFILE_QUERY_KEY,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return getTenantProfile(token);
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 5 * 60 * 1000,
  });
}
