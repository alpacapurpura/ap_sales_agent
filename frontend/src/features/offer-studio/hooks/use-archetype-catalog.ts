"use client";

import { useQuery } from "@tanstack/react-query";

import {
  archetypeCatalogApi,
  type ArchetypeCapabilities,
  type ArchetypeCatalogResponse,
} from "../api/archetype-catalog-api";

import type { OfferArchetype } from "../types";

const QUERY_KEY = ["offer", "archetypes", "catalog"] as const;

/**
 * Fetches the archetype capabilities catalog from the backend.
 *
 * Single source of truth for: supports_editions, wizard copy, edition nouns,
 * publishing constraints, default delivery/fulfillment, and display metadata.
 *
 * Cached for 1 hour because the catalog is domain metadata that only changes
 * on deploy — the backend bumps ``version`` to force cache eviction.
 */
export function useArchetypeCatalog() {
  return useQuery<ArchetypeCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: archetypeCatalogApi.fetch,
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/**
 * Returns the capabilities for a specific archetype, or ``undefined`` while
 * the catalog is still loading. Never returns ``null`` for a valid archetype
 * once loaded — the backend guarantees every enum value has an entry.
 */
export function useArchetypeCapabilities(
  archetype: OfferArchetype | undefined,
): ArchetypeCapabilities | undefined {
  const { data } = useArchetypeCatalog();
  if (!data || !archetype) return undefined;
  return data.archetypes.find((a) => a.archetype === archetype);
}
