import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import {
  Offer,
  AvatarDefinition,
  Objection,
} from "../types";
import { backendToFrontend, frontendToBackend, BackendOffer } from "./adapter";
import { OfferFormValues } from "../types/schema";

const API_URL = config.api.baseUrl;

export const offerApi = {
  listOffers: async (token: string): Promise<Offer[]> => {
    try {
        const url = `${API_URL}/api/v1/products/`;
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const res = await fetchClient(url, { 
                signal: controller.signal,
                headers: { 
                    Authorization: `Bearer ${token}` 
                }
            });
            clearTimeout(timeoutId);
            
            if (!res.ok) {
                const errorText = await res.text();
                throw new Error(`Failed to list offers: ${res.statusText}`);
            }
            const data: BackendOffer[] = await res.json();
            
            // Map backend response using adapter
            return data.map(backendToFrontend);

        } catch (fetchError: any) {
            clearTimeout(timeoutId);
            if (fetchError.name === 'AbortError') {
                throw new Error(`Request to ${url} timed out after 10 seconds`);
            }
            throw fetchError;
        }
    } catch (error) {
        console.error("Network error listing offers:", error);
        throw error;
    }
  },

  getOffer: async (id: string, token: string): Promise<Offer> => {
    const res = await fetchClient(`${API_URL}/api/v1/products/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to fetch offer");
    const item: BackendOffer = await res.json();
    return backendToFrontend(item);
  },
  
  createOffer: async (data: OfferFormValues, token: string) => {
       const payload = frontendToBackend(data);
       const res = await fetchClient(`${API_URL}/api/v1/products/`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error("Failed to create offer");
        return res.json();
  },
  
  saveOffer: async (id: string, data: Partial<OfferFormValues>, token: string) => {
      const payload = frontendToBackend(data);
      const res = await fetchClient(`${API_URL}/api/v1/products/${id}`, {
      method: "PATCH",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error("Failed to save offer");
    return res.json();
  },

  getAvatar: async () => { return { icp_description: "", anti_avatar: "", voice_tone_config: {} }; },
  saveAvatar: async (data: AvatarDefinition) => { return data; },
  saveObjections: async (offerId: string, objections: Objection[]) => { return objections; },
  uploadAsset: async (offerId: string, file: File) => { return { id: "mock", name: file.name, type: "PDF" }; },

  generatePsychology: async (data: {
    avatar_id: string;
    offer_name: string;
    offer_description?: string;
    current_pains: string[];
    current_desires: string[];
  }, token: string): Promise<{ pains: string[]; desires: string[] }> => {
    const res = await fetchClient(`${API_URL}/api/v1/offers/ai/psychology`, {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Error generating psychology");
    }
    return res.json();
  },

  getLandingConfig: async (offerId: string, token: string): Promise<any> => {
      const res = await fetchClient(`${API_URL}/api/v1/offers/${offerId}/landing`, {
          headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch landing config");
      return res.json();
  },

  generateLandingPage: async (offerId: string, token: string): Promise<any> => {
      const res = await fetchClient(`${API_URL}/api/v1/offers/${offerId}/landing/generate`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || "Error generating landing page");
      }
      return res.json();
  },

  updateLandingPage: async (offerId: string, config: any, token: string): Promise<any> => {
      const res = await fetchClient(`${API_URL}/api/v1/offers/${offerId}/landing`, {
          method: "PUT",
          headers: { 
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}` 
          },
          body: JSON.stringify(config)
      });
      if (!res.ok) {
          throw new Error("Failed to update landing page");
      }
      return res.json();
  },

  regenerateBlock: async (offerId: string, blockType: string, currentContent: any, instruction: string, token: string): Promise<any> => {
      const res = await fetchClient(`${API_URL}/api/v1/offers/${offerId}/landing/ai/regenerate-block`, {
          method: "POST",
          headers: { 
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}` 
          },
          body: JSON.stringify({
              block_type: blockType,
              current_content: currentContent,
              instruction: instruction
          })
      });
      if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || "Error regenerating block");
      }
      return res.json();
  }
};
