import { config } from "../config";
import { fetchClient } from "../http-client";

export interface OfferGalleryImage {
  id: string;
  tenant_id: string;
  offer_id: string;
  public_url: string;
  user_description: string;
  ai_description: string;
  ai_colors: string[];
  status: "processing" | "completed" | "failed";
  created_at: string;
}

const API_URL = config.api.baseUrl;

export const offerGalleryApi = {
  upload: async (
    token: string,
    offerId: string,
    file: File,
    description: string,
  ): Promise<OfferGalleryImage> => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("description", description);

    const res = await fetchClient(`${API_URL}/api/v1/assets/offers/${offerId}/gallery/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!res.ok) throw new Error("Upload failed");
    return res.json() as Promise<OfferGalleryImage>;
  },

  list: async (token: string, offerId: string): Promise<OfferGalleryImage[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/assets/offers/${offerId}/gallery`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to list images");
    return res.json() as Promise<OfferGalleryImage[]>;
  },

  delete: async (token: string, offerId: string, imageId: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/assets/offers/${offerId}/gallery/${imageId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!res.ok) throw new Error("Failed to delete image");
  },
};
