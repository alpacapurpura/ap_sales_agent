import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface GeneralSettings {
  default_currency: string;
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

export const settingsApi = {
  getGeneralSettings: async (token: string): Promise<GeneralSettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/general`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch general settings");
    return res.json();
  },

  getProfile: async (token: string): Promise<SystemUserProfile> => {
    const res = await fetch(`${API_URL}/api/v1/settings/profile`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch user profile");
    return res.json();
  },

  getAISettings: async (token: string): Promise<AISettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/ai`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch AI settings");
    return res.json();
  },

  updateAISettings: async (data: Partial<AISettings>, token: string): Promise<AISettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/ai`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update AI settings");
    return res.json();
  },

  getWebhookSettings: async (token: string): Promise<WebhookSettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/webhook`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to fetch webhook settings");
    return res.json();
  },

  regenerateWebhookSecret: async (token: string): Promise<WebhookSettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/webhook/regenerate`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!res.ok) throw new Error("Failed to regenerate webhook secret");
    return res.json();
  },

  updateGeneralSettings: async (
    data: GeneralSettings,
    token: string
  ): Promise<GeneralSettings> => {
    const res = await fetch(`${API_URL}/api/v1/settings/general`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update general settings");
    return res.json();
  },
};
