"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { settingsApi } from "@/lib/api/settings";

import type { Tenant } from "@/lib/api/settings";

/**
 *
 */
export function useTenants() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<Tenant[]>({
    queryKey: ["tenants"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return settingsApi.getTenants(token);
    },
    enabled: isLoaded && isSignedIn,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
