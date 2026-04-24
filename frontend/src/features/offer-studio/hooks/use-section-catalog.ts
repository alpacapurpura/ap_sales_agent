"use client";

import { useMemo } from "react";

import { resolveIconByName } from "../lib/icon-name-resolver";

import { useArchetypeCatalog } from "./use-archetype-catalog";

import type { SectionKey, SectionMetadata } from "../api/archetype-catalog-api";
import type { LucideIcon } from "lucide-react";

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

/**
 * Pure helper — resolve a display label for an arbitrary slug against the
 * loaded catalog map. Falls back to the slug itself when the catalog is
 * loading or the slug is unknown (keeps the UI graceful during first paint
 * + defensive for future slugs not yet in the enum).
 *
 * Exposed as a pure function (not a hook) so callers inside other pure
 * functions — e.g. ``buildCrumbs`` in ``OfferStudioBreadcrumb`` — can use
 * it without adding a Rules-of-Hooks violation.
 */
export function resolveSectionLabel(
  catalog: ReadonlyMap<SectionKey, SectionMetadata> | undefined,
  slug: string,
): string {
  return catalog?.get(slug as SectionKey)?.label_es ?? slug;
}

/**
 * Pure helper — resolve a Lucide icon component for a slug. Falls back to
 * ``Sparkles`` (via ``resolveIconByName``) when the catalog is loading or
 * the slug is unknown. Keeps surfaces alive during first paint.
 */
export function resolveSectionIcon(
  catalog: ReadonlyMap<SectionKey, SectionMetadata> | undefined,
  slug: string,
): LucideIcon {
  const meta = catalog?.get(slug as SectionKey);
  return resolveIconByName(meta?.icon_name);
}

/**
 * Pure helper — true when the catalog declares a section as ``collection``
 * (landing + detail routes, N-of-M items). False otherwise, including
 * while loading (conservative default: singleton).
 */
export function resolveIsCollection(
  catalog: ReadonlyMap<SectionKey, SectionMetadata> | undefined,
  slug: string,
): boolean {
  return catalog?.get(slug as SectionKey)?.kind === "collection";
}

/**
 * Convenience hook returning a stable label-resolver bound to the current
 * catalog. Consumers that need to resolve many slugs in the same render
 * (dropdowns, lists) prefer this over calling ``useSectionMetadata`` per
 * slug.
 */
export function useSectionLabelResolver(): (slug: string) => string {
  const catalog = useSectionCatalog();
  return useMemo(() => (slug: string) => resolveSectionLabel(catalog, slug), [catalog]);
}
