import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

/**
 * Stable identifier for a Brand Studio editor section.
 *
 * MUST mirror ``BrandSectionKey`` in
 * ``backend/src/modules/brand/domain/section_catalog.py`` verbatim. The
 * backend arch test ``test_brand_section_catalog_completeness`` fails CI
 * if the catalog drifts from the enum.
 */
export type BrandSectionKey =
  | "publico"
  | "identity"
  | "estilo"
  | "positioning"
  | "narrative"
  | "methodology"
  | "story"
  | "team"
  | "authority"
  | "testimonials"
  | "visuals"
  | "communication-assets"
  | "contact"
  | "legal";

/**
 * Editing UX mode. Mirrors ``offer-studio``'s equivalent type:
 *
 *  - ``singleton``: one form per section.
 *  - ``collection``: list-based section (landing + detail routes).
 */
export type BrandSectionKind = "singleton" | "collection";

export interface BrandSectionMetadata {
  readonly key: BrandSectionKey;
  readonly label_es: string;
  /** Lucide icon name in PascalCase. Resolved to a component on the frontend. */
  readonly icon_name: string;
  readonly kind: BrandSectionKind;
}

export interface BrandSectionCatalogResponse {
  readonly version: string;
  readonly sections: readonly BrandSectionMetadata[];
}

export const brandSectionCatalogApi = {
  async fetch(): Promise<BrandSectionCatalogResponse> {
    const res = await fetchClient(`${API_URL}/api/v1/brand/sections/catalog`);
    if (!res.ok) {
      throw new Error(`Failed to fetch brand section catalog: ${res.status}`);
    }
    return res.json() as Promise<BrandSectionCatalogResponse>;
  },
};
