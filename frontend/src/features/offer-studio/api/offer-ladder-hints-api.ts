import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferValueLevel } from "../types";
import type { ExpertBusinessType } from "@/features/tenant-profile/types/tenant-profile";

const API_URL = config.api.baseUrl;

/** Per-(business_type, value_level) ladder adaptation shipped flat from
 *  the backend. Frontend filters client-side by the tenant's primary
 *  business type. See ``backend/src/modules/offer/domain/offer_ladder_hints.py``. */
export interface LadderHint {
  readonly business_type: ExpertBusinessType;
  readonly value_level: OfferValueLevel;
  readonly examples_es: readonly string[];
  readonly typical_offer_type_es: string;
  /** ``null`` = use the universal ``ValueLevelMetadata`` fallback for this rung. */
  readonly typical_price_min_usd: number | null;
  readonly typical_price_max_usd: number | null;
}

export interface OfferLadderHintsCatalogResponse {
  readonly version: string;
  readonly hints: readonly LadderHint[];
}

export const offerLadderHintsApi = {
  fetch: async (): Promise<OfferLadderHintsCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/ladder-hints/catalog`);
    if (!res.ok) throw new Error("Failed to fetch offer-ladder-hints catalog");
    return res.json() as Promise<OfferLadderHintsCatalogResponse>;
  },
};
