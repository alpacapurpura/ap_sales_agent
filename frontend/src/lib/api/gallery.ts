import { fetchClient } from "../http-client";

export interface GalleryImage {
  id: string;
  tenant_id: string;
  public_url: string;
  user_description: string;
  ai_description: string;
  ai_colors: string[];
  status: "processing" | "completed" | "failed";
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export const galleryApi = {
  upload: async (token: string, file: File, description: string): Promise<GalleryImage> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("description", description);

    const res = await fetchClient(`${API_URL}/api/v1/gallery/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!res.ok) throw new Error("Upload failed");
    return res.json();
  },

  list: async (token: string): Promise<GalleryImage[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/gallery/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to list images");
    return res.json();
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/gallery/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to delete image");
  },
};
