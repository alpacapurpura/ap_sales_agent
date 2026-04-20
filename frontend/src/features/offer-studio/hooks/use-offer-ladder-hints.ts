"use client";

import { useMemo } from "react";

import { useQuery } from "@tanstack/react-query";

import {
  offerLadderHintsApi,
  type LadderHint,
  type OfferLadderHintsCatalogResponse,
} from "../api/offer-ladder-hints-api";

import type { ExpertBusinessType } from "@/features/tenant-profile/types/tenant-profile";
import type { OfferValueLevel } from "../types";

const QUERY_KEY = ["offer", "ladder-hints", "catalog"] as const;

/**
 * Fetches the full offer-ladder-hints catalog (45 entries = 9 business
 * types × 5 value-levels). Cached for 1 hour — this is domain metadata,
 * same shape as ``useValueLevelCatalog`` and ``useExpertBusinessTypesCatalog``.
 *
 * Consumers should prefer the ``useLadderHint`` / ``useLadderHintsForType``
 * helpers below, which index the response by the keys they actually need
 * instead of scanning the 45-entry array per render.
 */
export function useOfferLadderHints() {
  return useQuery<OfferLadderHintsCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: offerLadderHintsApi.fetch,
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/** Return the hint for one ``(business_type, value_level)`` pair, or
 *  ``undefined`` while loading. */
export function useLadderHint(
  businessType: ExpertBusinessType | undefined,
  valueLevel: OfferValueLevel | undefined,
): LadderHint | undefined {
  const { data } = useOfferLadderHints();
  return useMemo(() => {
    if (!data || !businessType || !valueLevel) return undefined;
    return data.hints.find(
      (h) => h.business_type === businessType && h.value_level === valueLevel,
    );
  }, [data, businessType, valueLevel]);
}

/** Return every hint for one business type, keyed by ``value_level``.
 *  Empty record while loading. */
export function useLadderHintsForType(
  businessType: ExpertBusinessType | undefined,
): Partial<Record<OfferValueLevel, LadderHint>> {
  const { data } = useOfferLadderHints();
  return useMemo(() => {
    if (!data || !businessType) return {};
    const out: Partial<Record<OfferValueLevel, LadderHint>> = {};
    for (const hint of data.hints) {
      if (hint.business_type === businessType) {
        out[hint.value_level] = hint;
      }
    }
    return out;
  }, [data, businessType]);
}
