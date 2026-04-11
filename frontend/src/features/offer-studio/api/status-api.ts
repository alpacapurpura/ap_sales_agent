import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import type {
  ChangeOfferStatusPayload,
  OfferStatusResponse,
} from "../types/lifecycle";

const API_URL = config.api.baseUrl;

export const statusApi = {
  change: async (
    offerId: string,
    payload: ChangeOfferStatusPayload,
    token: string,
  ): Promise<OfferStatusResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/offers/${offerId}/status`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      const errBody = (await res
        .json()
        .catch(() => ({ detail: res.statusText }))) as { detail?: string };
      throw new Error(errBody.detail ?? "Error al cambiar el estado");
    }
    return (await res.json()) as OfferStatusResponse;
  },
};
