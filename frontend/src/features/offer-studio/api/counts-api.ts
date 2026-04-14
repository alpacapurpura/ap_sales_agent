import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import type { OfferCountsResponse } from "../types/counts";

const API_URL = config.api.baseUrl;

export const countsApi = {
  get: async (offerId: string, token: string): Promise<OfferCountsResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/counts`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new Error(`Error al cargar los contadores: ${res.statusText}`);
    }
    return (await res.json()) as OfferCountsResponse;
  },
};
