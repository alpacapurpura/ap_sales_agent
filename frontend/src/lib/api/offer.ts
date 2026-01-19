export interface AvatarDefinition {
  id?: string;
  icp_description: string;
  anti_avatar: string;
  voice_tone_config: Record<string, any>;
}

export interface Offer {
  id?: string;
  name: string;
  price: number;
  promise: string;
  guarantees: string[];
  qualification_rules: string[];
  status?: string; // Added for dashboard
  avatar?: string; // Added for dashboard
  avatar_id?: string; // Added for backend sync
}

export interface Objection {
  id: string;
  trigger: string;
  strategy: string;
  script: string;
}

export interface MarketingAsset {
  id: string;
  name: string;
  type: "WEBINAR" | "VSL" | "PDF" | "URL" | "VIDEO";
  url?: string;
  size?: string;
}

import { config } from "../config";

const API_URL = config.api.baseUrl;

export const offerApi = {
  listOffers: async (): Promise<Offer[]> => {
    try {
        const url = `${API_URL}/api/v1/products/`;
        console.log(`[OfferAPI] Fetching offers from: ${url}`);
        
        // Add 10s timeout to prevent infinite loading
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const res = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (!res.ok) {
                const errorText = await res.text();
                console.error("Failed to list offers:", errorText);
                throw new Error(`Failed to list offers: ${res.statusText}`);
            }
            const data = await res.json();
            return data.map((item: any) => ({
              id: item.id,
              name: item.name,
              price: item.pricing?.amount || 0,
              // Normalize status to Title Case for UI consistency
              status: item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase() : "Draft",
              avatar: "Global", // TODO: Fetch avatar name if needed
              avatar_id: item.avatar_id,
              promise: item.metadata_info?.big_promise || "",
              guarantees: item.metadata_info?.guarantees || [],
              qualification_rules: item.metadata_info?.qualification_rules || []
            }));
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

  createOffer: async (name: string): Promise<Offer> => {
    try {
        const res = await fetch(`${API_URL}/api/v1/products/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, type: "program" })
        });
        if (!res.ok) {
            const errorText = await res.text();
            console.error("Failed to create offer:", errorText);
            throw new Error(`Failed to create offer: ${res.statusText}`);
        }
        const data = await res.json();
        return {
          id: data.id,
          name: data.name,
          price: 0,
          promise: "",
          guarantees: [],
          qualification_rules: [],
          avatar_id: data.avatar_id
        };
    } catch (error) {
        console.error("Network error creating offer:", error);
        throw error;
    }
  },

  getOffer: async (id: string): Promise<Offer> => {
    const res = await fetch(`${API_URL}/api/v1/products/${id}`);
    if (!res.ok) throw new Error("Failed to fetch offer");
    const data = await res.json();
    return {
      id: data.id,
      name: data.name,
      price: data.pricing?.amount || 0,
      promise: data.metadata_info?.big_promise || "",
      guarantees: data.metadata_info?.guarantees || [],
      qualification_rules: data.metadata_info?.qualification_rules || [],
      avatar_id: data.avatar_id
    };
  },

  getAvatar: async () => {
    // Deprecated: Use avatarApi.getAvatar instead
    return { icp_description: "", anti_avatar: "", voice_tone_config: {} };
  },
  
  saveAvatar: async (data: AvatarDefinition) => {
    // Deprecated: Use avatarApi.updateAvatar instead
    console.log("Saved Avatar (Deprecated)", data);
    return data;
  },

  saveOffer: async (id: string, data: Offer) => {
    const payload: any = {
      name: data.name,
      pricing: { amount: Number(data.price) },
      metadata_info: {
        big_promise: data.promise,
        guarantees: data.guarantees,
        qualification_rules: data.qualification_rules
      }
    };

    if (data.avatar_id) {
        payload.avatar_id = data.avatar_id;
    }
    
    const res = await fetch(`${API_URL}/api/v1/products/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) throw new Error("Failed to save offer");
    return res.json();
  },

  saveObjections: async (offerId: string, objections: Objection[]) => {
    console.log("Saved Objections", objections);
    return objections;
  },

  uploadAsset: async (offerId: string, file: File) => {
    console.log("Uploaded Asset", file.name);
    return { id: "mock-asset-id", name: file.name, type: "PDF", url: "http://mock" };
  }
};
