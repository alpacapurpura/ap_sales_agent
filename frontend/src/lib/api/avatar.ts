import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

// Buyer avatar persona definition — shared with offer-studio types
export interface AvatarDefinition {
  icp_description?: string;
  anti_avatar?: string;
  voice_tone_config?: Record<string, unknown>;
  pain_points?: string[];
  desires?: string[];
  awareness_level?: string;
  sophistication_level?: string;
}

export interface Avatar extends AvatarDefinition {
  id: string;
  name: string;
  is_default: boolean;
  scope: "GLOBAL" | "OFFER_SPECIFIC";
  created_at?: string;
}

export interface CreateAvatarDTO {
  name: string;
  icp_description?: string;
  anti_avatar?: string;
  voice_tone_config?: Record<string, unknown>;
  scope?: "GLOBAL" | "OFFER_SPECIFIC";
}

export const avatarApi = {
  listAvatars: async (token: string, scope = "GLOBAL"): Promise<Avatar[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/?scope=${scope}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list avatars");
    return res.json() as Promise<Avatar[]>;
  },

  getAvatar: async (token: string, id: string): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get avatar");
    return res.json() as Promise<Avatar>;
  },

  createAvatar: async (token: string, data: CreateAvatarDTO): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create avatar");
    return res.json() as Promise<Avatar>;
  },

  updateAvatar: async (
    token: string,
    id: string,
    data: Partial<CreateAvatarDTO>,
  ): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update avatar");
    return res.json() as Promise<Avatar>;
  },

  deleteAvatar: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete avatar");
  },

  setDefault: async (token: string, id: string): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/avatars/${id}/set-default`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to set default avatar");
    return res.json() as Promise<Avatar>;
  },
};
