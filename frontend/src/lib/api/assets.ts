import { fetchClient } from "../http-client";

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

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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
    const url = new URL(`${API_URL}/api/v1/assets/gallery/`);
    if (type) url.searchParams.append("type", type);

    const res = await fetchClient(url.toString(), {
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
