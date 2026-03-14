import { fetchClient } from "../http-client";
import { config } from "../config";

export interface Asset {
  id: string;
  tenant_id: string;
  offer_id?: string | null;
  type: "IMAGE" | "VIDEO" | "AUDIO" | "DOCUMENT";
  filename: string;
  mime_type?: string;
  public_url: string;
  user_description?: string;
  ai_metadata?: Record<string, any>;
  ai_description?: string; // Legacy/Mapped
  ai_colors?: string[]; // Legacy/Mapped
  status: "processing" | "completed" | "failed";
  created_at: string;
}

const API_URL = config.api.baseUrl;

export const assetsApi = {
  upload: async (token: string, file: File, description?: string, offer_id?: string): Promise<Asset> => {
    const formData = new FormData();
    formData.append("file", file);
    if (description) formData.append("description", description);
    if (offer_id) formData.append("offer_id", offer_id);

    const res = await fetchClient(`${API_URL}/api/v1/assets/gallery/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  },

  list: async (token: string, type?: string): Promise<Asset[]> => {
    // Build URL — supports both absolute (http://...) and relative (/api/...) API_URL
    let urlString = `${API_URL}/api/v1/assets/gallery/`;
    if (type) {
      const separator = urlString.includes("?") ? "&" : "?";
      urlString = `${urlString}${separator}type=${encodeURIComponent(type)}`;
    }

    const res = await fetchClient(urlString, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to list assets");
    return res.json();
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/assets/gallery/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to delete asset");
  },
};
