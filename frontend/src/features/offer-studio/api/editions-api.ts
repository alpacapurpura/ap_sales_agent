import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { LaunchEdition, LaunchEditionCreate, LaunchEditionUpdate } from "../types";

const API_URL = config.api.baseUrl;

export const editionsApi = {
  list: async (offerId: string, token: string): Promise<LaunchEdition[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/editions`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list editions");
    return res.json();
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
    return res.json();
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
    return res.json();
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
    return res.json();
  },
};
