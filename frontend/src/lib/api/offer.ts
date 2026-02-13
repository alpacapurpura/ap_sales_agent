import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

// --- ENUMS ---
export enum OfferValueLevel {
  N0 = "N0",
  N1 = "N1",
  N2 = "N2",
  N3 = "N3",
  N4 = "N4",
  N5 = "N5",
  N6 = "N6",
}

export enum OfferDeliveryModel {
  DIY = "DIY",
  DWY = "DWY",
  DFY = "DFY",
  B2B = "B2B",
}

export enum OfferType {
  FREE_RESOURCE = "FREE_RESOURCE",
  COMMUNITY_LITE = "COMMUNITY_LITE",
  CONTENT_ASSET_PODCAST = "CONTENT_ASSET_PODCAST",
  FREE_WEBINAR_CHALLENGE = "FREE_WEBINAR_CHALLENGE",
  TRIPWIRE_OFFER = "TRIPWIRE_OFFER",
  SELF_PACED_COURSE = "SELF_PACED_COURSE",
  PAID_NEWSLETTER_SUBSCRIPTION = "PAID_NEWSLETTER_SUBSCRIPTION",
  PHYSICAL_MERCH = "PHYSICAL_MERCH",
  HYBRID_MENTORSHIP = "HYBRID_MENTORSHIP",
  COHORT_BASED_COURSE = "COHORT_BASED_COURSE",
  GROUP_COACHING_PROGRAM = "GROUP_COACHING_PROGRAM",
  VIP_DAY_STRATEGY = "VIP_DAY_STRATEGY",
  ONE_ON_ONE_PRIVATE_MENTORING = "1ON1_PRIVATE_MENTORING",
  DEEP_DIVE_AUDIT = "DEEP_DIVE_AUDIT",
  PRODUCTIZED_SERVICE = "PRODUCTIZED_SERVICE",
  MONTHLY_RETAINER = "MONTHLY_RETAINER",
  PERFORMANCE_REV_SHARE = "PERFORMANCE_REV_SHARE",
  MASTERMIND_NETWORK = "MASTERMIND_NETWORK",
  LUXURY_RETREAT = "LUXURY_RETREAT",
  CORPORATE_TRAINING = "CORPORATE_TRAINING",
  BRAND_SPONSORSHIP = "BRAND_SPONSORSHIP",
  KEYNOTE_SPEAKING = "KEYNOTE_SPEAKING",
}

export enum OfferStatus {
  DRAFT = "DRAFT",
  ACTIVE = "ACTIVE",
  PAUSED = "PAUSED",
  ARCHIVED = "ARCHIVED",
  WAITLIST = "WAITLIST",
  SOLD_OUT = "SOLD_OUT",
}

export enum GuaranteeType {
  STANDARD_30_DAY = "STANDARD_30_DAY",
  CONDITIONAL_ACTION_BASED = "CONDITIONAL_ACTION_BASED",
  DOUBLE_MONEY_BACK = "DOUBLE_MONEY_BACK",
  NO_REFUNDS = "NO_REFUNDS",
}

export enum OnboardingMechanism {
  CHECKOUT_LINK = "SEND_LINK",
  CALENDAR_BOOKING = "BOOK_CALL",
  INTAKE_FORM = "INTAKE_FORM",
  COMMUNITY_INVITE = "JOIN_COMMUNITY"
}

// --- INTERFACES ---
export interface PricingStructure {
  label: string;
  plan_type?: string;
  total_amount: number;
  currency?: string;
  deposit_required?: number;
  number_of_installments?: number;
  installment_amount?: number;
}

export interface MarketingAsset {
  id: string;
  name: string;
  type: string;
  size?: string;
  url?: string;
}

export interface Offer {
  id: string;
  name: string;
  internal_sku?: string;
  type: OfferType;
  
  value_level: OfferValueLevel;
  delivery_model: OfferDeliveryModel;
  status: OfferStatus; // Mapped from backend string to Enum if possible, or just string

  headline_promise?: string;
  primary_outcome?: string;
  time_to_value?: string;
  
  pricing?: PricingStructure[];
  currency?: string;

  // Polymorphic details
  specific_details?: Record<string, any>;
  
  // Stats & Metadata
  active_clients?: number; // From specific_details or computed
  metadata_info?: Record<string, any>;
  
  avatar_id?: string;
  
  // Marketing Psychology
  marketing_pain_points?: string[];
  marketing_desires?: string[];

  // Deliverables
  deliverables?: DeliverableItem[];
  
  // Additional Fields
  target_avatar_match?: string[];
  prerequisites?: any[]; // Using any[] for now to match schema flexibility
  includes_offers?: string[];
  
  guarantee_type?: GuaranteeType;
  guarantee_terms?: string;
  access_duration_text?: string;
  instructors?: string[];

  onboarding_action?: OnboardingMechanism;
  onboarding_url?: string;
  calendar_type_id?: string;
  checkout_page_url?: string;
  vsl_link?: string;
  
  landing_page_config?: {
      is_published: boolean;
      slug: string;
      [key: string]: any;
  };
}

export interface DeliverableItem {
  name: string;
  format: string; // Should match DeliverableFormat enum values
  quantity: string;
  value_stack_price: number;
}

export interface AvatarDefinition {
    icp_description?: string;
    anti_avatar?: string;
    voice_tone_config?: Record<string, any>;
    pain_points?: string[];
    desires?: string[];
}

export interface Objection {
  id: string;
  trigger: string;
  strategy: string;
  script: string;
}

export const offerApi = {
  listOffers: async (token: string): Promise<Offer[]> => {
    try {
        const url = `${API_URL}/api/v1/products/`;
        
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
                throw new Error(`Failed to list offers: ${res.statusText}`);
            }
            const data = await res.json();
            
            // Map backend response to Offer Interface
            return data.map((item: any) => ({
                id: item.id,
                name: item.name,
                internal_sku: item.internal_sku,
                type: item.type as OfferType,
                
                // Ensure value_level is set (fallback or from backend)
                value_level: item.offer_value_level || item.value_level || "N0", 
                delivery_model: item.delivery_model || "DIY",
                status: (item.status?.toUpperCase() || "DRAFT") as OfferStatus,
                
                headline_promise: item.headline_promise,
                primary_outcome: item.primary_outcome,
                time_to_value: item.time_to_value,
                
                pricing: item.pricing,
                currency: item.currency || "USD",
                
                specific_details: item.specific_details || {},
                metadata_info: item.metadata_info || {},
                avatar_id: item.avatar_id,

                marketing_pain_points: item.marketing_pain_points || [],
                marketing_desires: item.marketing_desires || [],
                deliverables: item.deliverables || [],
                target_avatar_match: item.target_avatar_match || [],
                prerequisites: item.prerequisites || [],
                includes_offers: item.includes_offers || [],

                guarantee_type: item.guarantee_type,
                guarantee_terms: item.guarantee_terms,
                access_duration_text: item.access_duration_text,
                landing_page_config: item.landing_page_config
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

  getOffer: async (id: string, token: string): Promise<Offer> => {
    const res = await fetch(`${API_URL}/api/v1/products/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to fetch offer");
    const item = await res.json();
    return {
        id: item.id,
        name: item.name,
        internal_sku: item.internal_sku,
        type: item.type as OfferType,
        value_level: item.offer_value_level || item.value_level || "N0",
        delivery_model: item.delivery_model || "DIY",
        status: (item.status?.toUpperCase() || "DRAFT") as OfferStatus,
        headline_promise: item.headline_promise,
        primary_outcome: item.primary_outcome,
        time_to_value: item.time_to_value,
        pricing: item.pricing,
        currency: item.currency,
        specific_details: item.specific_details,
        metadata_info: item.metadata_info,
        avatar_id: item.avatar_id,
        marketing_pain_points: item.marketing_pain_points || [],
        marketing_desires: item.marketing_desires || [],
        deliverables: item.deliverables || [],
        target_avatar_match: item.target_avatar_match || [],
        prerequisites: item.prerequisites || [],
        includes_offers: item.includes_offers || [],
        
        guarantee_type: item.guarantee_type,
        guarantee_terms: item.guarantee_terms,
        // Map access duration fields from metadata
        access_duration: item.metadata_info?.access_duration || item.access_duration,
        access_duration_text: item.metadata_info?.access_duration_text || item.access_duration_text,
        support_duration_days: item.metadata_info?.support_duration_days || item.support_duration_days,
        instructors: item.instructors || [],
        landing_page_config: item.landing_page_config
    };
  },
  
  // Keep legacy signatures for now but return dummy or updated types
  createOffer: async (data: any, token: string) => {
      // Implementation omitted for brevity, assuming existing usage handles it or we'll fix it later
       const res = await fetch(`${API_URL}/api/v1/products/`, {
          method: "POST",
          headers: { 
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to create offer");
        return res.json();
  },
  
  saveOffer: async (id: string, data: any, token: string) => {
      const res = await fetch(`${API_URL}/api/v1/products/${id}`, {
      method: "PATCH",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(data)
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
    const res = await fetch(`${API_URL}/api/v1/offers/ai/psychology`, {
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
      const res = await fetch(`${API_URL}/api/v1/offers/${offerId}/landing`, {
          headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch landing config");
      return res.json();
  },

  generateLandingPage: async (offerId: string, token: string): Promise<any> => {
      const res = await fetch(`${API_URL}/api/v1/offers/${offerId}/landing/generate`, {
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
      const res = await fetch(`${API_URL}/api/v1/offers/${offerId}/landing`, {
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
      const res = await fetch(`${API_URL}/api/v1/offers/${offerId}/landing/ai/regenerate-block`, {
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
