"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  offerTypePresetCatalogApi,
  type ExpertBusinessType,
  type OfferTypePreset,
  type OfferTypePresetCatalogResponse,
} from "../api/offer-type-preset-catalog-api";

const QUERY_KEY_BASE = ["offer", "type-presets", "catalog"] as const;

const HOUR = 60 * 60 * 1000;

/**
 * Fetches the offer-type preset catalog from the backend.
 *
 * Pass the tenant's ``business_types`` to narrow the preset list to what
 * they actually sell (4-11 presets instead of 76). Omit for the admin /
 * discovery view.
 *
 * Cached for 1 hour — the backend bumps ``version`` to force eviction
 * when a preset is added or renamed.
 */
export function useOfferTypePresetCatalog(businessTypes: readonly ExpertBusinessType[] = []) {
  const key = [...QUERY_KEY_BASE, [...businessTypes].sort().join(",")] as const;
  return useQuery<OfferTypePresetCatalogResponse>({
    queryKey: key,
    queryFn: () => offerTypePresetCatalogApi.fetch(businessTypes),
    staleTime: HOUR,
    gcTime: 24 * HOUR,
  });
}

/**
 * Fetches the full catalog (no business_type filter). Used by admin
 * surfaces, audit views, and first-time discovery flows.
 */
export function useOfferTypePresetCatalogAll() {
  return useQuery<OfferTypePresetCatalogResponse>({
    queryKey: [...QUERY_KEY_BASE, "all"] as const,
    queryFn: offerTypePresetCatalogApi.fetchAll,
    staleTime: HOUR,
    gcTime: 24 * HOUR,
  });
}

/**
 * Returns a specific preset by id, or ``undefined`` while loading.
 */
export function useOfferTypePreset(
  presetId: string | undefined,
  businessTypes: readonly ExpertBusinessType[] = [],
): OfferTypePreset | undefined {
  const { data } = useOfferTypePresetCatalog(businessTypes);
  return useMemo(() => {
    if (!data || !presetId) return undefined;
    return data.presets.find((p) => p.preset_id === presetId);
  }, [data, presetId]);
}

/**
 * Groups presets by their internal archetype tag. Useful for admin UIs
 * that want to visualise archetype coverage.
 */
export function usePresetsByArchetype(businessTypes: readonly ExpertBusinessType[] = []) {
  const { data } = useOfferTypePresetCatalog(businessTypes);
  return useMemo(() => {
    if (!data) return undefined;
    const groups = new Map<string, OfferTypePreset[]>();
    for (const preset of data.presets) {
      const bucket = groups.get(preset.archetype) ?? [];
      bucket.push(preset);
      groups.set(preset.archetype, bucket);
    }
    return groups;
  }, [data]);
}
