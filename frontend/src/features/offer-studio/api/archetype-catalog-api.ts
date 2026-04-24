import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferArchetype, VariantStructure } from "../types";

export type { VariantStructure };

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

/**
 * Editing UX mode for a section (Fase 03 · Block A).
 *
 * - ``singleton``: single-form section (identity, promise, pricing, etc.).
 * - ``collection``: list-based section with landing + detail routes
 *   (testimonials, portfolio, faq, gallery, instructors).
 */
export type SectionKind = "singleton" | "collection";

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
  /** Fase 03 · Block A — drives FE rail/form-runtime rendering. */
  readonly kind: SectionKind;
}

export interface ArchetypeCapabilities {
  readonly archetype: OfferArchetype;
  readonly supports_editions: boolean;
  readonly edition_noun_es: string;
  readonly edition_noun_plural_es: string;
  readonly requires_start_date_on_publish: boolean;
  readonly requires_end_date_on_publish: boolean;
  readonly requires_location_on_publish: boolean;
  readonly supports_capacity: boolean;
  readonly supports_waitlist: boolean;
  readonly default_delivery: string;
  readonly default_fulfillment: string;
  /** Sprint 15.1 — default variant structure assigned to the placeholder
   *  edition spawned at offer creation. ``null`` iff the archetype does not
   *  support editions (defensive — post-15.1 every archetype supports
   *  variants). */
  readonly default_variant_structure: VariantStructure | null;
  /** Sprint 15.1 — tuple of accepted structures. Drives the wizard's
   *  "¿cómo varía tu oferta?" step when length > 1 and preset doesn't
   *  force a specific structure. */
  readonly supported_variant_structures: readonly VariantStructure[];
  /** Sprint 15.1 — when true, UX may collapse a 1-variant offer into a
   *  direct editor without rendering the collection landing. */
  readonly allow_single_variant: boolean;
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
