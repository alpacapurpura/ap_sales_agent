import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface CurrencyMetadata {
  readonly code: string;
  readonly label_es: string;
  readonly symbol: string;
  readonly countries_es: readonly string[];
  readonly decimal_digits: number;
}

export interface CurrencyCatalogResponse {
  readonly version: string;
  readonly currencies: readonly CurrencyMetadata[];
}

export const currencyCatalogApi = {
  fetch: async (): Promise<CurrencyCatalogResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/shared/currencies/catalog`);
    if (!res.ok) throw new Error("Failed to fetch currency catalog");
    return res.json() as Promise<CurrencyCatalogResponse>;
  },
};
