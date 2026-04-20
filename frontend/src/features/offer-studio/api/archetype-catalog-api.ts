import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferArchetype } from "../types";

const API_URL = config.api.baseUrl;

/**
 * Spanish copy for the 'will this offer have editions?' wizard step.
 * Present only for archetypes that support editions.
 */
export interface EditionsWizardCopy {
  readonly title: string;
  readonly description: string;
  readonly yes_label: string;
  readonly no_label: string;
}

export type EditionStructure = "none" | "single_date" | "cohort" | "recurring";

/**
 * Stable identifier for an Offer Studio editor section.
 *
 * MUST mirror ``SectionKey`` in
 * ``backend/src/modules/offer/domain/section_catalog.py`` verbatim. The
 * frontend arch test ``test-section-catalog-frontend-alignment`` fails CI
 * if the backend catalog adds or drops a key not reflected here.
 *
 * Changes here require a coordinated backend change — never add a key on
 * only one side.
 */
export type SectionKey =
  | "identity"
  | "strategy"
  | "psychology"
  | "promise"
  | "value_stack"
  | "instructors"
  | "knowledge"
  | "closing"
  | "product_details"
  | "subscription_details"
  | "gallery"
  | "event_details"
  | "pricing"
  | "program_details"
  | "service_details"
  | "resources"
  // Nuevas (Latam mass-market rollout)
  | "faq"
  | "testimonials"
  | "portfolio"
  | "location"
  | "platform_details";

/**
 * Persistence scope of a section — which aggregate its fields write to.
 *
 * - ``offer_level``: persists to the ``Offer`` row. Shared across editions.
 * - ``edition_level``: persists to a ``LaunchEdition``. Hidden under the
 *   virtual ``evergreen`` URL code.
 * - ``mixed``: per-field owner split. The form-runtime dispatcher routes
 *   each field's save based on its declared ``owner``.
 */
export type SectionScope = "offer_level" | "edition_level" | "mixed";

export interface SectionMetadata {
  readonly key: SectionKey;
  readonly label_es: string;
  readonly subtitle_es: string;
  /** Rich copilot-friendly context (2-4 sentences). Backend-only invariant: at
   *  least 1.5x longer than subtitle_es. */
  readonly help_text_es: string;
  /** Lucide icon name in PascalCase. Resolved to a component on the frontend. */
  readonly icon_name: string;
  readonly scope: SectionScope;
  /** Weight in per-offer completeness scoring, [0.1, 1.0]. */
  readonly completion_weight: number;
  /** Whether the section blocks offer publishing when empty. */
  readonly required_to_publish: boolean;
}

export interface ArchetypeCapabilities {
  readonly archetype: OfferArchetype;
  readonly supports_editions: boolean;
  readonly edition_structure: EditionStructure;
  readonly edition_noun_es: string;
  readonly edition_noun_plural_es: string;
  readonly requires_start_date_on_publish: boolean;
  readonly requires_end_date_on_publish: boolean;
  readonly requires_location_on_publish: boolean;
  readonly supports_capacity: boolean;
  readonly supports_waitlist: boolean;
  readonly default_delivery: string;
  readonly default_fulfillment: string;
  readonly label_es: string;
  readonly subtitle_es: string;
  readonly icon_name: string;
  readonly examples_es: readonly string[];
  readonly editions_wizard_copy: EditionsWizardCopy | null;
  /**
   * Ordered sections this archetype surfaces in the editor. Full metadata
   * is inlined so the nav rail renders without a second lookup.
   */
  readonly sections: readonly SectionMetadata[];
}

export interface ArchetypeCatalogResponse {
  readonly version: string;
  readonly archetypes: readonly ArchetypeCapabilities[];
  /**
   * Global section metadata — lets clients resolve any ``SectionKey``
   * referenced anywhere (copilot tools, future modules) without having to
   * page through every archetype entry.
   */
  readonly section_catalog: readonly SectionMetadata[];
}

export const archetypeCatalogApi = {
  fetch: async (): Promise<ArchetypeCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/archetypes/catalog`);
    if (!res.ok) throw new Error("Failed to fetch archetype catalog");
    return res.json() as Promise<ArchetypeCatalogResponse>;
  },
};
