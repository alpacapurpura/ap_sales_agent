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
    // Ensure valid URL construction even if API_URL is relative
    const base = API_URL.startsWith("http") ? undefined : "http://localhost";
    const url = new URL(`${API_URL}/api/v1/assets/gallery/`, base);
    
    if (type) url.searchParams.append("type", type);

    // If we used a dummy base, we might want to return relative path, 
    // but fetchClient handles absolute URLs fine.
    const urlString = base ? url.pathname + url.search : url.toString();

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
