import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferArchetype } from "../types";

const API_URL = config.api.baseUrl;

export interface EditionsWizardCopy {
  readonly title: string;
  readonly description: string;
  readonly yes_label: string;
  readonly no_label: string;
}

export type EditionStructure = "none" | "single_date" | "cohort" | "recurring";

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
  readonly icon_name: string;
  readonly editions_wizard_copy: EditionsWizardCopy | null;
}

export interface ArchetypeCatalogResponse {
  readonly version: string;
  readonly archetypes: readonly ArchetypeCapabilities[];
}

export const archetypeCatalogApi = {
  fetch: async (): Promise<ArchetypeCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/archetypes/catalog`);
    if (!res.ok) throw new Error("Failed to fetch archetype catalog");
    return res.json() as Promise<ArchetypeCatalogResponse>;
  },
};
