import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  EditionClonePayload,
  EditionCloneResponse,
  EditionLandingResponse,
  LaunchEdition,
  LaunchEditionCreate,
  LaunchEditionUpdate,
} from "../types";

const API_URL = config.api.baseUrl;

const readErrorDetail = async (res: Response, fallback: string): Promise<string> => {
  const body = (await res.json().catch(() => ({ detail: res.statusText }))) as { detail?: string };
  return body.detail ?? fallback;
};

export const editionsApi = {
  list: async (offerId: string, token: string): Promise<LaunchEdition[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/editions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list editions");
    return res.json() as Promise<LaunchEdition[]>;
  },

  create: async (
    offerId: string,
    data: LaunchEditionCreate,
    token: string,
  ): Promise<LaunchEdition> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/editions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create edition");
    return res.json() as Promise<LaunchEdition>;
  },

  update: async (
    offerId: string,
    editionId: string,
    data: LaunchEditionUpdate,
    token: string,
  ): Promise<LaunchEdition> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
    );
    if (!res.ok) throw new Error("Failed to update edition");
    return res.json() as Promise<LaunchEdition>;
  },

  delete: async (offerId: string, editionId: string, token: string): Promise<void> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error("Failed to delete edition");
  },

  duplicate: async (offerId: string, editionId: string, token: string): Promise<LaunchEdition> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}/duplicate`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error("Failed to duplicate edition");
    return res.json() as Promise<LaunchEdition>;
  },

  clone: async (
    offerId: string,
    editionId: string,
    payload: EditionClonePayload,
    token: string,
  ): Promise<EditionCloneResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}/clone`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al clonar la edición"));
    }
    return (await res.json()) as EditionCloneResponse;
  },

  getEditionLanding: async (
    offerId: string,
    editionId: string,
    token: string,
  ): Promise<EditionLandingResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}/landing`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al cargar el landing de la edición"));
    }
    return (await res.json()) as EditionLandingResponse;
  },
};
