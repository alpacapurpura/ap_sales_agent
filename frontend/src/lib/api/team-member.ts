import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

export interface TeamMember {
  id: string;
  tenant_id: string;
  name: string;
  role: string | null;
  bio: string | null;
  headshot_url: string | null;
  is_primary_voice: boolean;
  gender: string | null;
  communication_style: string | null;
  personal_website: string | null;
  personal_linkedin: string | null;
  personal_instagram: string | null;
  personal_tiktok: string | null;
  personal_facebook: string | null;
  work_whatsapp: string | null;
  gallery: string[];
  sort_order: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TeamMemberCreateDTO {
  name: string;
  role?: string;
  bio?: string;
  headshot_url?: string;
  is_primary_voice?: boolean;
  gender?: string;
  communication_style?: string;
  personal_website?: string;
  personal_linkedin?: string;
  personal_instagram?: string;
  personal_tiktok?: string;
  personal_facebook?: string;
  work_whatsapp?: string;
  gallery?: string[];
  sort_order?: number;
}

export type TeamMemberUpdateDTO = Partial<
  Pick<
    TeamMember,
    | "name"
    | "role"
    | "bio"
    | "headshot_url"
    | "is_primary_voice"
    | "gender"
    | "communication_style"
    | "personal_website"
    | "personal_linkedin"
    | "personal_instagram"
    | "personal_tiktok"
    | "personal_facebook"
    | "work_whatsapp"
    | "gallery"
    | "sort_order"
  >
>;

const BASE = `${API_URL}/api/v1/social-proof/team`;

export const teamMemberApi = {
  list: async (token: string): Promise<TeamMember[]> => {
    const res = await fetchClient(`${BASE}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list team members");
    return res.json() as Promise<TeamMember[]>;
  },

  get: async (token: string, id: string): Promise<TeamMember> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get team member");
    return res.json() as Promise<TeamMember>;
  },

  create: async (token: string, data: TeamMemberCreateDTO): Promise<TeamMember> => {
    const res = await fetchClient(`${BASE}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create team member");
    return res.json() as Promise<TeamMember>;
  },

  patch: async (token: string, id: string, data: TeamMemberUpdateDTO): Promise<TeamMember> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update team member");
    return res.json() as Promise<TeamMember>;
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete team member");
  },

  clone: async (token: string, id: string): Promise<TeamMember> => {
    const res = await fetchClient(`${BASE}/${id}/clone`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to clone team member");
    return res.json() as Promise<TeamMember>;
  },
};
