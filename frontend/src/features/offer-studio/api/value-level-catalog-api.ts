import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { OfferValueLevel } from "../types";

const API_URL = config.api.baseUrl;

export interface ValueLevelMetadata {
  readonly value_level: OfferValueLevel;
  readonly order: number;
  readonly label_es: string;
  readonly description_es: string;
  readonly role_in_funnel_es: string;
  readonly icon_name: string;
  readonly examples_es: readonly string[];
  readonly is_free: boolean;
  readonly typical_price_min_usd: number | null;
  readonly typical_price_max_usd: number | null;
}

export interface ValueLevelCatalogResponse {
  readonly version: string;
  readonly value_levels: readonly ValueLevelMetadata[];
}

export const valueLevelCatalogApi = {
  fetch: async (): Promise<ValueLevelCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/value-levels/catalog`);
    if (!res.ok) throw new Error("Failed to fetch value-level catalog");
    return res.json() as Promise<ValueLevelCatalogResponse>;
  },
};
