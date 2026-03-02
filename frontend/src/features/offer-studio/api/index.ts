import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import {
  Offer,
  AvatarDefinition,
  Objection,
} from "../types";
import { backendToFrontend, frontendToBackend, BackendOffer } from "./adapter";
import { OfferFormValues } from "../types/schema";
import { MOCK_OFFERS } from "./mock-data";
import { ENABLE_MOCKS as USE_MOCK_DATA } from "@/lib/mock-config";

const API_URL = config.api.baseUrl;

export { USE_MOCK_DATA }; // Re-export for potential consumers

export const offerApi = {
  listOffers: async (token: string): Promise<Offer[]> => {
    if (USE_MOCK_DATA) {
        console.log("🔸 Using Mock Data for listOffers");
        await new Promise(resolve => setTimeout(resolve, 800));
        return MOCK_OFFERS;
    }

    try {
        const url = `${API_URL}/api/v1/offer/products/`;
        
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
    if (USE_MOCK_DATA) {
        console.log(`🔸 Using Mock Data for getOffer: ${id}`);
        await new Promise(resolve => setTimeout(resolve, 500));
        const mockOffer = MOCK_OFFERS.find(o => o.id === id);
        if (mockOffer) return mockOffer;
        // Si no se encuentra en los mocks explícitos, devolver el primero como fallback o error
        console.warn(`Mock offer ${id} not found, returning first mock offer`);
        return MOCK_OFFERS[0];
    }

    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to fetch offer");
    const item: BackendOffer = await res.json();
    return backendToFrontend(item);
  },
  
  createOffer: async (data: OfferFormValues, token: string) => {
       if (USE_MOCK_DATA) {
           console.log("🔸 Using Mock Data for createOffer", data);
           await new Promise(resolve => setTimeout(resolve, 1000));
           return {
               id: `mock-new-${Date.now()}`,
               ...data,
               created_at: new Date().toISOString(),
               updated_at: new Date().toISOString()
           };
       }

       const payload = frontendToBackend(data);
       const res = await fetchClient(`${API_URL}/api/v1/offer/products/`, {
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
      if (USE_MOCK_DATA) {
          console.log(`🔸 Using Mock Data for saveOffer: ${id}`, data);
          await new Promise(resolve => setTimeout(resolve, 600));
          return { id, ...data, success: true };
      }

      const payload = frontendToBackend(data);
      const res = await fetchClient(`${API_URL}/api/v1/offer/products/${id}`, {
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

  saveSection: async (id: string, sectionId: string, data: any, token: string) => {
    if (USE_MOCK_DATA) {
        console.log(`🔸 Using Mock Data for saveSection: ${sectionId}`, data);
        await new Promise(resolve => setTimeout(resolve, 600));
        return { success: true, section: sectionId, data };
    }

    let endpoint = "";
    let payload = data;

    switch (sectionId) {
        case "identity":
            endpoint = "/identity";
            break;
        case "strategy":
            endpoint = "/strategy";
            break;
        case "promise":
            endpoint = "/promise";
            break;
        case "psychology":
            endpoint = "/psychology";
            break;
        case "pricing":
            endpoint = "/pricing";
            if (data.pricing_options) {
                payload = { pricing_options: data.pricing_options };
            } else if (data.pricing) {
                payload = { pricing_options: data.pricing };
            }
            break;
        case "closing":
            endpoint = "/closing";
            break;
        case "instructors":
            endpoint = "/instructors";
            break;
        case "value_stack":
            endpoint = "/value_stack";
            break;
        case "resources":
            endpoint = "/resources";
            break;
        case "gallery":
            endpoint = "/visuals";
            break;
        case "program_details":
        case "product_details":
        case "service_details":
        case "event_details":
        case "subscription_details":
            endpoint = "/details";
            // Fix: Send data directly to avoid double nesting specific_details.
            // data already contains { specific_details: {...}, access_duration: ... }
            payload = data;
            break;
        default:
            console.warn(`No specific endpoint for section ${sectionId}, falling back to generic patch`);
            return offerApi.saveOffer(id, data, token);
    }

    const res = await fetchClient(`${API_URL}/api/v1/offer/products/${id}${endpoint}`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });

    if (!res.ok) {
        throw new Error(`Failed to save section ${sectionId}`);
    }
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
    if (USE_MOCK_DATA) {
        console.log("🔸 Using Mock Data for generatePsychology");
        await new Promise(resolve => setTimeout(resolve, 1500));
        return {
            pains: ["Miedo al fracaso", "Falta de tiempo", "Inseguridad tecnológica", "Presupuesto limitado"],
            desires: ["Libertad financiera", "Reconocimiento", "Automatización total", "Impacto global"]
        };
    }

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
      if (USE_MOCK_DATA) {
          return null; 
      }
      // Corregido: Endpoint específico de Landing Module
      const res = await fetchClient(`${API_URL}/api/v1/landings/offer/${offerId}`, {
          headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch landing config");
      return res.json();
  },

  generateLandingPage: async (offerId: string, token: string): Promise<any> => {
      if (USE_MOCK_DATA) {
          console.log("🔸 Using Mock Data for generateLandingPage");
          await new Promise(resolve => setTimeout(resolve, 2000));
          return {
              slug: `offer-${offerId}`,
              is_published: false,
              sections: []
          };
      }
      // Corregido: POST a /api/v1/landings/ con offer_id en body
      const res = await fetchClient(`${API_URL}/api/v1/landings/`, {
          method: "POST",
          headers: { 
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}` 
            },
          body: JSON.stringify({ 
              offer_id: offerId,
              slug: `offer-${offerId}-${Date.now()}` // Slug temporal
          })
      });
      if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: res.statusText }));
          throw new Error(err.detail || "Error generating landing page");
      }
      return res.json();
  },

  updateLandingPage: async (offerId: string, config: any, token: string): Promise<any> => {
      if (USE_MOCK_DATA) {
          console.log("🔸 Using Mock Data for updateLandingPage");
          await new Promise(resolve => setTimeout(resolve, 500));
          return config;
      }
      // Corregido: PATCH a /api/v1/landings/offer/{offerId}
      const res = await fetchClient(`${API_URL}/api/v1/landings/offer/${offerId}`, {
          method: "PATCH",
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
      if (USE_MOCK_DATA) {
          console.log("🔸 Using Mock Data for regenerateBlock");
          await new Promise(resolve => setTimeout(resolve, 1500));
          return {
              ...currentContent,
              headline: "Título Regenerado por IA (Mock)",
              subheadline: "Este es un texto simulado generado como respuesta a tu instrucción."
          };
      }
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
