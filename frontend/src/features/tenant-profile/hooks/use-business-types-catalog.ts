"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { getBusinessTypesCatalog } from "../api/tenant-profile-api";

import type { BusinessTypesCatalogResponse } from "../types/tenant-profile";

export const BUSINESS_TYPES_CATALOG_QUERY_KEY = [
  "tenant-profile",
  "business-types-catalog",
] as const;

/**
 * Fetches the business-types catalog.
 *
 * Near-immutable enum metadata — stale time is 24 h.
 * The backend bumps ``version`` to force eviction when the catalog changes.
 *
 * CONTRACT §6.1 — GET /api/v1/catalogs/business-types
 */
export function useBusinessTypesCatalog() {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<BusinessTypesCatalogResponse>({
    queryKey: BUSINESS_TYPES_CATALOG_QUERY_KEY,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return getBusinessTypesCatalog(token);
    },
    enabled: isLoaded && isSignedIn === true,
    staleTime: 24 * 60 * 60 * 1000,
    gcTime: 48 * 60 * 60 * 1000,
  });
}
