"use client";

import { useArchetypeCatalog } from "./use-archetype-catalog";

import type { SectionMetadata } from "../api/archetype-catalog-api";
import type { OfferArchetype } from "../types";

/**
 * Returns the ordered section metadata list for an archetype.
 *
 * Returns ``undefined`` while the catalog is loading. Never returns ``null``
 * or an empty list for a valid archetype — the backend guarantees every
 * archetype declares at least one section (``test_every_archetype_declares_sections``).
 */
export function useSectionsForArchetype(
  archetype: OfferArchetype | undefined,
): readonly SectionMetadata[] | undefined {
  const { data } = useArchetypeCatalog();
  if (!data || !archetype) return undefined;
  return data.archetypes.find((a) => a.archetype === archetype)?.sections;
}
