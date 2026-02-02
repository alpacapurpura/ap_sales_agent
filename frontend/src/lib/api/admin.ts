import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  can_use_platform_keys: boolean;
  openai_api_key_set: boolean;
  gemini_api_key_set: boolean;
}

export const adminApi = {
  getTenants: async (token: string): Promise<Tenant[]> => {
    const res = await fetchClient(`${config.api.baseUrl}/api/v1/admin/tenants`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to fetch tenants");
    return res.json();
  },

  updateTenantPermissions: async (token: string, tenantId: string, canUsePlatformKeys: boolean) => {
    const res = await fetchClient(`${config.api.baseUrl}/api/v1/admin/tenants/${tenantId}/permissions`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ can_use_platform_keys: canUsePlatformKeys }),
    });
    if (!res.ok) throw new Error("Failed to update permissions");
    return res.json();
  }
};
