import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface Offer {
  id?: string;
  name: string; // public_name
  internal_sku?: string;
  type?: string;
  delivery_model?: string;
  
  price: number; // calculated from pricing_options[0] or simple field
  currency?: string;
  
  promise: string; // headline_promise
  primary_outcome?: string;
  time_to_value?: string;
  target_avatar_match?: string[];
  
  guarantees: string[]; // Legacy
  qualification_rules: string[]; // Legacy
  
  requires_application?: boolean;
  min_financial_capacity?: string;
  prerequisites?: string[];
  
  pricing_options?: any[];
  guarantee_type?: string;
  guarantee_terms?: string;
  
  downsell_offer_id?: string;
  upsell_offer_id?: string;
  includes_offers?: string[];
  deliverables?: any[];
  specific_details?: any;
  
  vsl_link?: string;
  checkout_page_url?: string;
  calendar_type_id?: string;
  
  status?: string;
  avatar?: string;
  avatar_id?: string;
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

export const offerApi = {
  listOffers: async (token: string): Promise<Offer[]> => {
    try {
        const url = `${API_URL}/api/v1/products/`;
        console.log(`[OfferAPI] Fetching offers from: ${url}`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);
        
        try {
            const res = await fetch(url, { 
                signal: controller.signal,
                headers: { 
                    Authorization: `Bearer ${token}` 
                }
            });
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
              type: item.type,
              price: item.pricing?.length > 0 ? (item.pricing[0].total_amount || item.pricing[0].amount) : (item.pricing?.amount || 0),
              currency: item.currency || "USD",
              status: item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase() : "Draft",
              avatar: "Global",
              avatar_id: item.avatar_id,
              promise: item.headline_promise || item.metadata_info?.big_promise || "",
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

  createOffer: async (data: Partial<Offer>, token: string): Promise<Offer> => {
    try {
        const res = await fetch(`${API_URL}/api/v1/products/`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        });
        if (!res.ok) {
            const errorText = await res.text();
            console.error("Failed to create offer:", errorText);
            throw new Error(`Failed to create offer: ${res.statusText}`);
        }
        const resData = await res.json();
        
        if (!resData.id) {
            throw new Error("Created offer is missing ID");
        }

        return {
          id: resData.id,
          name: resData.name,
          price: 0,
          promise: "",
          guarantees: [],
          qualification_rules: [],
          avatar_id: resData.avatar_id
        };
    } catch (error) {
        console.error("Network error creating offer:", error);
        throw error;
    }
  },

  getOffer: async (id: string, token: string): Promise<Offer> => {
    if (!id || id === 'undefined' || id === 'null') {
        throw new Error("Invalid Offer ID");
    }

    const res = await fetch(`${API_URL}/api/v1/products/${id}`, {
        headers: { 
            Authorization: `Bearer ${token}` 
        }
    });
    if (!res.ok) throw new Error("Failed to fetch offer");
    const data = await res.json();
    
    // Map backend response to Frontend Offer Interface
    return {
      id: data.id,
      internal_sku: data.internal_sku,
      name: data.name,
      type: data.type,
      delivery_model: data.delivery_model,
      
      // Pricing logic: Try to get from pricing_options list or legacy simple pricing
      price: data.pricing?.length > 0 ? data.pricing[0].total_amount : (data.pricing?.amount || 0),
      currency: data.currency || "USD",
      pricing_options: Array.isArray(data.pricing) ? data.pricing : [],
      
      promise: data.headline_promise || data.metadata_info?.big_promise || "",
      primary_outcome: data.primary_outcome,
      time_to_value: data.time_to_value,
      target_avatar_match: data.target_avatar_match || [],
      
      requires_application: data.requires_application,
      min_financial_capacity: data.min_financial_capacity,
      prerequisites: data.prerequisites || [],
      
      guarantee_type: data.guarantee_type,
      guarantee_terms: data.guarantee_terms,
      guarantees: data.metadata_info?.guarantees || [], // Legacy
      qualification_rules: data.metadata_info?.qualification_rules || [], // Legacy
      
      downsell_offer_id: data.downsell_product_id,
      upsell_offer_id: data.upsell_product_id,
      includes_offers: data.includes_offers || [],
      deliverables: data.deliverables || [],
      specific_details: data.specific_details || {},
      
      vsl_link: data.metadata_info?.vsl_link,
      checkout_page_url: data.metadata_info?.checkout_page_url,
      calendar_type_id: data.metadata_info?.calendar_type_id,
      
      status: data.status,
      avatar_id: data.avatar_id
    };
  },

  saveOffer: async (id: string, data: Offer, token: string) => {
    // Map Frontend Offer to Backend Payload
    const payload: any = {
      name: data.name,
      internal_sku: data.internal_sku,
      type: data.type,
      delivery_model: data.delivery_model,
      
      headline_promise: data.promise,
      primary_outcome: data.primary_outcome,
      time_to_value: data.time_to_value,
      target_avatar_match: data.target_avatar_match,
      
      requires_application: data.requires_application,
      min_financial_capacity: data.min_financial_capacity,
      prerequisites: data.prerequisites,
      
      pricing: data.pricing_options, // Backend expects 'pricing' as JSONB
      currency: data.currency,
      
      guarantee_type: data.guarantee_type,
      guarantee_terms: data.guarantee_terms,
      
      downsell_product_id: data.downsell_offer_id || null, // Handle empty string as null
      upsell_product_id: data.upsell_offer_id || null,
      includes_offers: data.includes_offers,
      deliverables: data.deliverables,
      specific_details: data.specific_details,
      
      status: data.status,
      avatar_id: data.avatar_id,
      
      metadata_info: {
        // Preserve existing metadata or update
        vsl_link: data.vsl_link,
        checkout_page_url: data.checkout_page_url,
        calendar_type_id: data.calendar_type_id,
        // Legacy support
        big_promise: data.promise,
        guarantees: data.guarantees,
        qualification_rules: data.qualification_rules
      }
    };
    
    // Clean up nulls/undefined if necessary
    
    const res = await fetch(`${API_URL}/api/v1/products/${id}`, {
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
  uploadAsset: async (offerId: string, file: File) => { return { id: "mock", name: file.name, type: "PDF" }; }
};
