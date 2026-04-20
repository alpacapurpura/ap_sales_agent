import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferArchetype, OfferDeliveryModel } from "../types";

const API_URL = config.api.baseUrl;

export interface FormatMetadata {
  readonly format_id: string;
  readonly archetype: OfferArchetype;
  readonly label_es: string;
  readonly description_es: string;
  readonly icon_name: string;
  readonly format_hint: string;
  readonly delivery_model: OfferDeliveryModel;
  /** Score per ExpertBusinessType, 0.0..1.0. Absent = 0.0. */
  readonly suitable_for: Readonly<Record<string, number>>;
  readonly tags: readonly string[];
  readonly specific_details_defaults: Readonly<Record<string, unknown>>;
}

export interface FormatCatalogResponse {
  readonly version: string;
  readonly formats: readonly FormatMetadata[];
}

export interface FormatCatalogParams {
  readonly archetype?: OfferArchetype;
  /** ExpertBusinessType values. Comma-joined server-side. */
  readonly businessTypes?: readonly string[];
}

export const formatCatalogApi = {
  fetch: async (params: FormatCatalogParams = {}): Promise<FormatCatalogResponse> => {
    const query = new URLSearchParams();
    if (params.archetype) query.set("archetype", params.archetype);
    if (params.businessTypes && params.businessTypes.length > 0) {
      query.set("business_types", params.businessTypes.join(","));
    }
    const qs = query.toString();
    const url = qs
      ? `${API_URL}/api/v1/offer/formats/catalog?${qs}`
      : `${API_URL}/api/v1/offer/formats/catalog`;
    const res = await fetchClient(url);
    if (!res.ok) throw new Error("Failed to fetch format catalog");
    return res.json() as Promise<FormatCatalogResponse>;
  },
};
