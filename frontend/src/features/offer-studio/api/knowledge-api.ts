// Offer knowledge sources API adapter — CONTRACT.md §5.4
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  KnowledgeListQuery,
  KnowledgeListResponse,
  KnowledgeSourceResponse,
  KnowledgeUrlIngestPayload,
} from "../types/knowledge";

const API_URL = config.api.baseUrl;

const buildQueryString = (query?: KnowledgeListQuery): string => {
  if (!query) return "";
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.type) params.set("type", query.type);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
};

const readErrorDetail = async (res: Response, fallback: string): Promise<string> => {
  const body = (await res.json().catch(() => ({ detail: res.statusText }))) as { detail?: string };
  return body.detail ?? fallback;
};

export const knowledgeApi = {
  list: async (
    offerId: string,
    query: KnowledgeListQuery | undefined,
    token: string,
  ): Promise<KnowledgeListResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/knowledge${buildQueryString(query)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al cargar las fuentes de conocimiento"));
    }
    return (await res.json()) as KnowledgeListResponse;
  },

  upload: async (offerId: string, file: File, token: string): Promise<KnowledgeSourceResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/knowledge/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al subir el archivo de conocimiento"));
    }
    return (await res.json()) as KnowledgeSourceResponse;
  },

  addUrl: async (
    offerId: string,
    payload: KnowledgeUrlIngestPayload,
    token: string,
  ): Promise<KnowledgeSourceResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${offerId}/knowledge/url`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al registrar la URL"));
    }
    return (await res.json()) as KnowledgeSourceResponse;
  },

  remove: async (offerId: string, sourceId: string, token: string): Promise<void> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/knowledge/${sourceId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al eliminar la fuente"));
    }
  },

  reindex: async (
    offerId: string,
    sourceId: string,
    token: string,
  ): Promise<KnowledgeSourceResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/knowledge/${sourceId}/reindex`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al reindexar la fuente"));
    }
    return (await res.json()) as KnowledgeSourceResponse;
  },
};
