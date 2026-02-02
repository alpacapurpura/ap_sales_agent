import { AvatarDefinition } from "./offer";
import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

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
  voice_tone_config?: Record<string, any>;
  scope?: "GLOBAL" | "OFFER_SPECIFIC";
}

export const avatarApi = {
  listAvatars: async (token: string, scope: string = "GLOBAL"): Promise<Avatar[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/?scope=${scope}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list avatars");
    return res.json();
  },

  getAvatar: async (token: string, id: string): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get avatar");
    return res.json();
  },

  createAvatar: async (token: string, data: CreateAvatarDTO): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create avatar");
    return res.json();
  },

  updateAvatar: async (token: string, id: string, data: Partial<CreateAvatarDTO>): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/${id}`, {
      method: "PATCH",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update avatar");
    return res.json();
  },

  deleteAvatar: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete avatar");
  },

  setDefault: async (token: string, id: string): Promise<Avatar> => {
    const res = await fetchClient(`${API_URL}/api/v1/avatars/${id}/set-default`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to set default avatar");
    return res.json();
  },
};
