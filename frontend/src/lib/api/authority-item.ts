import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

export type AuthorityType =
  | "certification"
  | "award"
  | "media_mention"
  | "published_work"
  | "client_logo"
  | "credential"
  | "partnership"
  | "speaking"
  | "podcast"
  | "other";

export interface AuthorityItem {
  id: string;
  tenant_id: string;
  entity_name: string;
  authority_type: AuthorityType;
  context: string | null;
  proof_url: string | null;
  logo_url: string | null;
  obtained_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AuthorityCreateDTO {
  entity_name: string;
  authority_type: AuthorityType;
  context?: string;
  proof_url?: string;
  logo_url?: string;
  obtained_at?: string;
  expires_at?: string;
}

export type AuthorityUpdateDTO = Partial<
  Pick<
    AuthorityItem,
    | "entity_name"
    | "authority_type"
    | "context"
    | "proof_url"
    | "logo_url"
    | "obtained_at"
    | "expires_at"
    | "is_active"
  >
>;

const BASE = `${API_URL}/api/v1/social-proof/authority`;

export const authorityApi = {
  list: async (token: string): Promise<AuthorityItem[]> => {
    const res = await fetchClient(`${BASE}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list authority items");
    return res.json() as Promise<AuthorityItem[]>;
  },

  get: async (token: string, id: string): Promise<AuthorityItem> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get authority item");
    return res.json() as Promise<AuthorityItem>;
  },

  create: async (token: string, data: AuthorityCreateDTO): Promise<AuthorityItem> => {
    const res = await fetchClient(`${BASE}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create authority item");
    return res.json() as Promise<AuthorityItem>;
  },

  patch: async (token: string, id: string, data: AuthorityUpdateDTO): Promise<AuthorityItem> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update authority item");
    return res.json() as Promise<AuthorityItem>;
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete authority item");
  },

  clone: async (token: string, id: string): Promise<AuthorityItem> => {
    const res = await fetchClient(`${BASE}/${id}/clone`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to clone authority item");
    return res.json() as Promise<AuthorityItem>;
  },
};
