"use client";

import { useMemo } from "react";

import { useSectionsForArchetype } from "./use-sections-for-archetype";

import type { SectionMetadata } from "../api/archetype-catalog-api";
import type { OfferArchetype } from "../types";

/** Reserved URL code for "no edition, offer-level content only". Never collides
 *  with a numeric edition_number. Mirrors the backend contract in D19. */
export const EVERGREEN_CODE = "evergreen";

/** URL segment identifying which edition an editor page is scoped to. Either
 *  the literal ``EVERGREEN_CODE`` or the string representation of an edition
 *  number (e.g. ``"1"``, ``"42"``). Resolved to a ``LaunchEdition`` row by
 *  ``useOfferEditionResolver`` (Phase D). */
export type EditionCode = string;

/**
 * Returns the sections that should be rendered for the given archetype at
 * the current edition-code URL segment.
 *
 * - On the virtual ``evergreen`` URL, ``edition_level`` sections are hidden
 *   because they need a ``LaunchEdition`` row to save against.
 * - On a specific-edition URL (numeric code), every section is visible —
 *   ``offer_level`` sections edit the shared offer row, ``edition_level``
 *   sections edit the launch row, ``mixed`` sections dispatch per field.
 *
 * Returns ``undefined`` while the catalog is loading.
 */
export function useVisibleSections(
  archetype: OfferArchetype | undefined,
  code: EditionCode | undefined,
): readonly SectionMetadata[] | undefined {
  const sections = useSectionsForArchetype(archetype);

  return useMemo(() => {
    if (!sections || !code) return sections;
    if (code !== EVERGREEN_CODE) return sections;
    return sections.filter((section) => section.scope !== "edition_level");
  }, [sections, code]);
}
