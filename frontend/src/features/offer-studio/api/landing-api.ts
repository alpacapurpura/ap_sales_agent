// Offer landing API adapter — CONTRACT.md §5.2
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import type {
  LandingGenerateResponse,
  LandingPublishResponse,
  LandingStatusResponse,
  LandingUnpublishResponse,
} from "../types/landing-status";

const API_URL = config.api.baseUrl;

const readErrorDetail = async (
  res: Response,
  fallback: string,
): Promise<string> => {
  const body = (await res
    .json()
    .catch(() => ({ detail: res.statusText }))) as { detail?: string };
  return body.detail ?? fallback;
};

export const landingApi = {
  getStatus: async (
    offerId: string,
    token: string,
  ): Promise<LandingStatusResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/landing/status`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al cargar el estado de la landing"),
      );
    }
    return (await res.json()) as LandingStatusResponse;
  },

  generate: async (
    offerId: string,
    token: string,
  ): Promise<LandingGenerateResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/landing/generate`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al generar la landing"),
      );
    }
    return (await res.json()) as LandingGenerateResponse;
  },

  regenerate: async (
    offerId: string,
    token: string,
  ): Promise<LandingGenerateResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/landing/regenerate`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al regenerar la landing"),
      );
    }
    return (await res.json()) as LandingGenerateResponse;
  },

  publish: async (
    offerId: string,
    token: string,
  ): Promise<LandingPublishResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/landing/publish`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al publicar la landing"),
      );
    }
    return (await res.json()) as LandingPublishResponse;
  },

  unpublish: async (
    offerId: string,
    token: string,
  ): Promise<LandingUnpublishResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/landing/unpublish`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al despublicar la landing"),
      );
    }
    return (await res.json()) as LandingUnpublishResponse;
  },
};
