import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

export type TestimonialMediaType = "text" | "video" | "audio" | "image";

export interface Testimonial {
  id: string;
  tenant_id: string;
  author_name: string;
  author_role: string | null;
  author_avatar_url: string | null;
  content: string | null;
  media_type: TestimonialMediaType;
  media_url: string | null;
  rating: number | null;
  source_url: string | null;
  captured_at: string | null;
  language: string;
  tags: string[];
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface TestimonialCreateDTO {
  author_name: string;
  author_role?: string;
  author_avatar_url?: string;
  content?: string;
  media_type?: TestimonialMediaType;
  media_url?: string;
  rating?: number;
  source_url?: string;
  captured_at?: string;
  language?: string;
  tags?: string[];
}

export type TestimonialUpdateDTO = Partial<
  Pick<
    Testimonial,
    | "author_name"
    | "author_role"
    | "author_avatar_url"
    | "content"
    | "media_type"
    | "media_url"
    | "rating"
    | "source_url"
    | "captured_at"
    | "language"
    | "tags"
    | "is_active"
  >
>;

const BASE = `${API_URL}/api/v1/social-proof/testimonials`;

export const testimonialApi = {
  list: async (token: string): Promise<Testimonial[]> => {
    const res = await fetchClient(`${BASE}/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list testimonials");
    return res.json() as Promise<Testimonial[]>;
  },

  get: async (token: string, id: string): Promise<Testimonial> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get testimonial");
    return res.json() as Promise<Testimonial>;
  },

  create: async (token: string, data: TestimonialCreateDTO): Promise<Testimonial> => {
    const res = await fetchClient(`${BASE}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create testimonial");
    return res.json() as Promise<Testimonial>;
  },

  patch: async (token: string, id: string, data: TestimonialUpdateDTO): Promise<Testimonial> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update testimonial");
    return res.json() as Promise<Testimonial>;
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${BASE}/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete testimonial");
  },

  clone: async (token: string, id: string): Promise<Testimonial> => {
    const res = await fetchClient(`${BASE}/${id}/clone`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to clone testimonial");
    return res.json() as Promise<Testimonial>;
  },
};
