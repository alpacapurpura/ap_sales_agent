// Offer assets API adapter — CONTRACT.md §5.3
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import type {
  AssetGeneratePayload,
  AssetListQuery,
  AssetListResponse,
  AssetResponse,
  AssetUpdatePayload,
} from "../types/assets";

const API_URL = config.api.baseUrl;

const buildQueryString = (query?: AssetListQuery): string => {
  if (!query) return "";
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.type) params.set("type", query.type);
  if (query.source) params.set("source", query.source);
  if (query.sort) params.set("sort", query.sort);
  if (typeof query.limit === "number") params.set("limit", String(query.limit));
  if (typeof query.offset === "number")
    params.set("offset", String(query.offset));
  const qs = params.toString();
  return qs ? `?${qs}` : "";
};

const readErrorDetail = async (
  res: Response,
  fallback: string,
): Promise<string> => {
  const body = (await res
    .json()
    .catch(() => ({ detail: res.statusText }))) as { detail?: string };
  return body.detail ?? fallback;
};

export const assetsApi = {
  list: async (
    offerId: string,
    query: AssetListQuery | undefined,
    token: string,
  ): Promise<AssetListResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets${buildQueryString(query)}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al cargar los recursos"),
      );
    }
    return (await res.json()) as AssetListResponse;
  },

  get: async (
    offerId: string,
    assetId: string,
    token: string,
  ): Promise<AssetResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets/${assetId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al cargar el recurso"));
    }
    return (await res.json()) as AssetResponse;
  },

  upload: async (
    offerId: string,
    file: File,
    token: string,
  ): Promise<AssetResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets/upload`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      },
    );
    if (!res.ok) {
      throw new Error(await readErrorDetail(res, "Error al subir el recurso"));
    }
    return (await res.json()) as AssetResponse;
  },

  generate: async (
    offerId: string,
    payload: AssetGeneratePayload,
    token: string,
  ): Promise<AssetResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets/generate`,
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
      throw new Error(
        await readErrorDetail(res, "Error al generar el recurso"),
      );
    }
    return (await res.json()) as AssetResponse;
  },

  update: async (
    offerId: string,
    assetId: string,
    payload: AssetUpdatePayload,
    token: string,
  ): Promise<AssetResponse> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets/${assetId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al actualizar el recurso"),
      );
    }
    return (await res.json()) as AssetResponse;
  },

  remove: async (
    offerId: string,
    assetId: string,
    token: string,
  ): Promise<void> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/assets/${assetId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) {
      throw new Error(
        await readErrorDetail(res, "Error al eliminar el recurso"),
      );
    }
  },

  getDownloadUrl: (offerId: string, assetId: string): string =>
    `${API_URL}/api/v1/offer/products/${offerId}/assets/${assetId}/download`,
};
