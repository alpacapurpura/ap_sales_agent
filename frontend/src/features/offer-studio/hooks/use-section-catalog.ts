"use client";

import { useMemo } from "react";

import { useArchetypeCatalog } from "./use-archetype-catalog";

import type { SectionKey, SectionMetadata } from "../api/archetype-catalog-api";

/**
 * Returns the global section catalog keyed by ``SectionKey``.
 *
 * Use this when you need metadata for an arbitrary section key without
 * going through the archetype. Returns ``undefined`` while loading.
 *
 * The returned map is memoized against the catalog payload so consumers
 * can use it in dependency arrays without triggering re-renders on every
 * catalog fetch.
 */
export function useSectionCatalog(): ReadonlyMap<SectionKey, SectionMetadata> | undefined {
  const { data } = useArchetypeCatalog();

  return useMemo(() => {
    if (!data) return undefined;
    const map = new Map<SectionKey, SectionMetadata>();
    for (const meta of data.section_catalog) {
      map.set(meta.key, meta);
    }
    return map;
  }, [data]);
}

/**
 * Looks up metadata for a single ``SectionKey``. Returns ``undefined``
 * while the catalog is loading. Once loaded, the key is guaranteed to
 * resolve because backend arch tests keep enum and catalog aligned.
 */
export function useSectionMetadata(key: SectionKey | undefined): SectionMetadata | undefined {
  const catalog = useSectionCatalog();
  if (!catalog || !key) return undefined;
  return catalog.get(key);
}
