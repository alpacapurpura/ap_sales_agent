import { AvatarDefinition } from "./offer";
import { config } from "../config";

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
  listAvatars: async (scope: string = "GLOBAL"): Promise<Avatar[]> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/?scope=${scope}`);
    if (!res.ok) throw new Error("Failed to list avatars");
    return res.json();
  },

  getAvatar: async (id: string): Promise<Avatar> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/${id}`);
    if (!res.ok) throw new Error("Failed to get avatar");
    return res.json();
  },

  createAvatar: async (data: CreateAvatarDTO): Promise<Avatar> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create avatar");
    return res.json();
  },

  updateAvatar: async (id: string, data: Partial<CreateAvatarDTO>): Promise<Avatar> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update avatar");
    return res.json();
  },

  deleteAvatar: async (id: string): Promise<void> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/${id}`, {
      method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete avatar");
  },

  setDefault: async (id: string): Promise<Avatar> => {
    const res = await fetch(`${API_URL}/api/v1/avatars/${id}/set-default`, {
      method: "POST",
    });
    if (!res.ok) throw new Error("Failed to set default avatar");
    return res.json();
  },
};
