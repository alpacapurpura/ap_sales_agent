"use client";

import { useQuery } from "@tanstack/react-query";

import {
  expertBusinessTypesApi,
  type ExpertBusinessTypesCatalogResponse,
  type ExpertBusinessTypeMetadata,
  type ExpertBusinessType,
} from "../api/expert-business-types-api";

const QUERY_KEY = ["brand", "expert-business-types", "catalog"] as const;

/**
 * Fetches the expert-business-type catalog. Drives both the first-time
 * onboarding wizard (Brand Studio) and the Offer Studio wizard's format
 * filter (matches ``format.suitable_for`` against the tenant's selected
 * business types).
 *
 * Cached for 1 hour — the catalog is domain metadata.
 */
export function useExpertBusinessTypesCatalog() {
  return useQuery<ExpertBusinessTypesCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: expertBusinessTypesApi.fetchCatalog,
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/** Return the metadata for a specific type, or ``undefined`` while loading. */
export function useExpertBusinessTypeMetadata(
  businessType: ExpertBusinessType | undefined,
): ExpertBusinessTypeMetadata | undefined {
  const { data } = useExpertBusinessTypesCatalog();
  if (!data || !businessType) return undefined;
  return data.business_types.find((t) => t.business_type === businessType);
}
