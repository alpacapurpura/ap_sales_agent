"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  brandSectionCatalogApi,
  type BrandSectionCatalogResponse,
  type BrandSectionKey,
  type BrandSectionMetadata,
} from "../api/section-catalog-api";
import { resolveBrandIconByName } from "../lib/icon-name-resolver";

import type { LucideIcon } from "lucide-react";

const QUERY_KEY = ["brand", "sections", "catalog"] as const;

/**
 * Fetches the brand-studio section catalog from the backend.
 *
 * Mirror of ``useArchetypeCatalog`` (offer-studio). Cached for 1 hour —
 * the backend bumps ``version`` to force cache eviction on deploy.
 *
 * Fase 03 · Block D — reemplaza el array hardcoded
 * ``BRAND_SECTIONS`` que vivía en ``lib/section-catalog.ts``.
 */
export function useBrandSectionCatalog() {
  return useQuery<BrandSectionCatalogResponse>({
    queryKey: QUERY_KEY,
    queryFn: () => brandSectionCatalogApi.fetch(),
    staleTime: 60 * 60 * 1000,
    gcTime: 24 * 60 * 60 * 1000,
  });
}

/**
 * Returns the catalog keyed by ``BrandSectionKey``. Useful for O(1) lookups
 * across multiple renders. Returns ``undefined`` while loading.
 */
export function useBrandSectionMap():
  | ReadonlyMap<BrandSectionKey, BrandSectionMetadata>
  | undefined {
  const { data } = useBrandSectionCatalog();
  return useMemo(() => {
    if (!data) return undefined;
    const map = new Map<BrandSectionKey, BrandSectionMetadata>();
    for (const meta of data.sections) {
      map.set(meta.key, meta);
    }
    return map;
  }, [data]);
}

/**
 * Pure helper — resolve a display label against the loaded brand catalog.
 * Falls back to the slug itself while loading or for unknown slugs.
 */
export function resolveBrandSectionLabel(
  catalog: ReadonlyMap<BrandSectionKey, BrandSectionMetadata> | undefined,
  slug: string,
): string {
  return catalog?.get(slug as BrandSectionKey)?.label_es ?? slug;
}

/**
 * Pure helper — resolve a Lucide icon for a brand slug.
 */
export function resolveBrandSectionIcon(
  catalog: ReadonlyMap<BrandSectionKey, BrandSectionMetadata> | undefined,
  slug: string,
): LucideIcon {
  return resolveBrandIconByName(catalog?.get(slug as BrandSectionKey)?.icon_name);
}

/**
 * Convenience hook returning a stable label-resolver bound to the current
 * catalog. Consumers that need to resolve many slugs in the same render
 * (dropdowns, lists) prefer this over calling ``useBrandSectionMap`` +
 * manual lookups.
 */
export function useBrandSectionLabelResolver(): (slug: string) => string {
  const catalog = useBrandSectionMap();
  return useMemo(() => (slug: string) => resolveBrandSectionLabel(catalog, slug), [catalog]);
}
