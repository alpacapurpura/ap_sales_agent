import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

export interface BuyerPersona {
  id: string;
  name: string;
  tagline: string | null;
  scope: "GLOBAL" | "OFFER" | "CAMPAIGN";
  offer_id: string | null;
  is_primary: boolean;
  demographics: Record<string, unknown>;
  psychographics: Record<string, unknown>;
  pain_points: Record<string, unknown>[];
  desires: Record<string, unknown>[];
  objections: Record<string, unknown>[];
  preferred_channels: Record<string, unknown>[];
  buyer_journey: Record<string, unknown>;
  purchase_triggers: string[];
  anti_patterns: string[];
  completeness_score: number;
  interview_session_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface BuyerPersonaCreateDTO {
  name: string;
  tagline?: string;
  scope?: "GLOBAL" | "OFFER" | "CAMPAIGN";
  offer_id?: string;
}

export type BuyerPersonaSectionUpdateDTO = Partial<
  Pick<
    BuyerPersona,
    | "name"
    | "tagline"
    | "demographics"
    | "psychographics"
    | "pain_points"
    | "desires"
    | "objections"
    | "preferred_channels"
    | "buyer_journey"
    | "purchase_triggers"
    | "anti_patterns"
  >
>;

export const buyerPersonaApi = {
  list: async (token: string): Promise<BuyerPersona[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list buyer personas");
    return res.json() as Promise<BuyerPersona[]>;
  },

  get: async (token: string, id: string): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get buyer persona");
    return res.json() as Promise<BuyerPersona>;
  },

  create: async (token: string, data: BuyerPersonaCreateDTO): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create buyer persona");
    return res.json() as Promise<BuyerPersona>;
  },

  patch: async (
    token: string,
    id: string,
    data: BuyerPersonaSectionUpdateDTO,
  ): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update buyer persona");
    return res.json() as Promise<BuyerPersona>;
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete buyer persona");
  },
};
