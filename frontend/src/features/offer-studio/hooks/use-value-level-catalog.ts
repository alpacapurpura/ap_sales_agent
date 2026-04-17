"use client";

import { useQuery } from "@tanstack/react-query";

import {
  valueLevelCatalogApi,
  type ValueLevelCatalogResponse,
  type ValueLevelMetadata,
} from "../api/value-level-catalog-api";

import type { OfferValueLevel } from "../types";

const QUERY_KEY = ["offer", "value-levels", "catalog"] as const;

/**
 * Fetches the value-level (ladder rung) catalog from the backend.
 *
 * Single source of truth for: label, description, role-in-funnel copy, icon,
 * examples, funnel ordering, and typical price ranges. Replaces the scattered
 * VALUE_LEVEL_LABELS + inline LEVEL_RICH_INFO dicts in frontend components.
 *
 * Cached for 1 hour — catalog only changes on deploy.
 */
export function useValueLevelCatalog() {
  return useQuery<ValueLevelCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: valueLevelCatalogApi.fetch,
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/** Return the metadata for a specific rung, or ``undefined`` while loading. */
export function useValueLevelMetadata(
  valueLevel: OfferValueLevel | undefined,
): ValueLevelMetadata | undefined {
  const { data } = useValueLevelCatalog();
  if (!data || !valueLevel) return undefined;
  return data.value_levels.find((v) => v.value_level === valueLevel);
}
