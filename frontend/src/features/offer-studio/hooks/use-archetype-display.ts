"use client";

import { resolveIconByName } from "../lib/icon-name-resolver";

import { useArchetypeCapabilities } from "./use-archetype-catalog";

import type { OfferArchetype } from "../types";
import type { LucideIcon } from "lucide-react";

export interface ArchetypeDisplay {
  readonly archetype: OfferArchetype;
  readonly label: string;
  readonly subtitle: string;
  readonly icon: LucideIcon;
  readonly examples: readonly string[];
}

/**
 * Returns the UI-ready presentation payload for an archetype: label,
 * subtitle, resolved Lucide icon component, and canonical example list.
 *
 * Returns ``undefined`` while the catalog is loading or for an unknown
 * archetype — callers render skeletons or defaults in that state.
 *
 * This hook replaces the former ``ARCHETYPE_METADATA`` hardcoded map in
 * ``config/archetype-metadata.ts`` — the frontend now has a single source
 * of truth on the backend (``/offer/archetypes/catalog``).
 */
export function useArchetypeDisplay(
  archetype: OfferArchetype | undefined,
): ArchetypeDisplay | undefined {
  const capabilities = useArchetypeCapabilities(archetype);
  if (!capabilities) return undefined;
  return {
    archetype: capabilities.archetype,
    label: capabilities.label_es,
    subtitle: capabilities.subtitle_es,
    icon: resolveIconByName(capabilities.icon_name),
    examples: capabilities.examples_es,
  };
}
