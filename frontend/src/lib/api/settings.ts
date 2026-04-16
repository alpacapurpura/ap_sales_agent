import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface GeneralSettings {
  default_currency: string;
  timezone: string | null;
}

export interface WebhookSettings {
  webhook_url: string;
  webhook_secret: string | null;
}

export interface AISettings {
  openai_api_key: string | null;
  gemini_api_key: string | null;
  can_use_platform_keys: boolean;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export interface TenantProfile {
  id: string;
  name: string;
  slug: string;
}

export interface SystemUserProfile {
  id: string;
  full_name: string | null;
  email: string;
  tenant: TenantProfile | null;
}

export interface BrandVisuals {
  primary_color: string;
  accent_color: string;
  background_color?: string;
  text_primary_color?: string;
  text_on_primary?: string;
  font_heading: string;
  font_body: string;
  design_style?: string;
}

export interface BrandStrategy {
  unique_value_proposition?: string;
  methodology_name?: string;
}

export interface BrandSettings {
  visuals: BrandVisuals;
  strategy: BrandStrategy;
  positioning?: {
    unique_value_proposition?: string;
  };
}

export interface TeamMember {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface TeamMemberCreate {
  full_name: string;
  email: string;
  password: string;
}

export const settingsApi = {
  getTenants: async (token: string): Promise<Tenant[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/users/me/tenants`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch tenants");
    return res.json() as Promise<Tenant[]>;
  },

  getTeam: async (token: string): Promise<TeamMember[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/team`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch team members");
    return res.json() as Promise<TeamMember[]>;
  },

  createTeamMember: async (data: TeamMemberCreate, token: string): Promise<TeamMember> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/team`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = (await res.json()) as { detail?: string };
      throw new Error(err.detail || "Failed to create team member");
    }
    return res.json() as Promise<TeamMember>;
  },

  getGeneralSettings: async (token: string): Promise<GeneralSettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/general`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch general settings");
    return res.json() as Promise<GeneralSettings>;
  },

  getProfile: async (token: string): Promise<SystemUserProfile> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
    });
    if (!res.ok) throw new Error("Failed to fetch user profile");
    return res.json() as Promise<SystemUserProfile>;
  },

  getAISettings: async (token: string): Promise<AISettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/ai`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch AI settings");
    return res.json() as Promise<AISettings>;
  },

  updateAISettings: async (data: Partial<AISettings>, token: string): Promise<AISettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/ai`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update AI settings");
    return res.json() as Promise<AISettings>;
  },

  getWebhookSettings: async (token: string): Promise<WebhookSettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/webhook`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch webhook settings");
    return res.json() as Promise<WebhookSettings>;
  },

  getBrandSettings: async (token: string): Promise<BrandSettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/settings`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch brand settings");
    return res.json() as Promise<BrandSettings>;
  },

  regenerateWebhookSecret: async (token: string): Promise<WebhookSettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/webhook/regenerate`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to regenerate webhook secret");
    return res.json() as Promise<WebhookSettings>;
  },

  updateGeneralSettings: async (
    data: Partial<GeneralSettings>,
    token: string,
  ): Promise<GeneralSettings> => {
    const res = await fetchClient(`${API_URL}/api/v1/iam/settings/general`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update general settings");
    return res.json() as Promise<GeneralSettings>;
  },
};
