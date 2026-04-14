// Offer campaigns API adapter — CONTRACT.md §5.5
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import type { OfferCampaignsQuery, OfferCampaignsResponse } from "../types/campaigns";

const API_URL = config.api.baseUrl;

const buildQueryString = (query?: OfferCampaignsQuery): string => {
  if (!query) return "";
  const params = new URLSearchParams();
  if (query.status) params.set("status", query.status);
  if (query.channel) params.set("channel", query.channel);
  if (query.period_start) params.set("period_start", query.period_start);
  if (query.period_end) params.set("period_end", query.period_end);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
};

export const campaignsApi = {
  list: async (
    offerId: string,
    query: OfferCampaignsQuery | undefined,
    token: string,
  ): Promise<OfferCampaignsResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/campaigns${buildQueryString(query)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      const body = (await res.json().catch(() => ({ detail: res.statusText }))) as {
        detail?: string;
      };
      throw new Error(body.detail ?? "Error al cargar las campañas");
    }
    return (await res.json()) as OfferCampaignsResponse;
  },
};
