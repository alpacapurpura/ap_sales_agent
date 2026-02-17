import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface BrandIdentity {
    brand_name?: string;
    legal_name?: string;
    tax_id?: string;
    fiscal_address?: string;
    website?: string;
    industry?: string;
    logo_url?: string;
    timezone?: string;
    language?: string;
    
    // Identity
    tagline?: string;
    description?: string;
    founding_year?: string;

    // Legal
    legal_representative?: string;
    terms_url?: string;
    privacy_url?: string;
}

export interface BrandStoryMilestone {
    id: string;
    year: string;
    title: string;
    description?: string;
}

export interface BrandStory {
    origin_story?: string;
    milestones: BrandStoryMilestone[];
}

export interface BrandCompetitor {
    id: string;
    name: string;
    differentiation?: string;
}

export interface BrandLogos {
    primary?: string;
    secondary?: string;
    dark_mode?: string;
    light_mode?: string;
}

export interface BrandMethodologyPillar {
    id: string;
    title: string;
    description?: string;
}

export interface BrandStrategy {
    unique_value_proposition?: string;
    competitors: BrandCompetitor[];
    methodology_name?: string;
    methodology_description?: string;
    methodology_pillars: BrandMethodologyPillar[];
}

export interface KeyFigure {
    id: string;
    name: string;
    role?: string;
    is_primary_voice: boolean;
    bio?: string;
    gender?: "Masculino" | "Femenino" | "Neutro";
    communication_style?: string;
    headshot_url?: string;
    gallery?: string[];
    personal_website?: string;
    personal_linkedin?: string;
    personal_instagram?: string;
    personal_tiktok?: string;
    personal_facebook?: string;
    work_whatsapp?: string;
}

export interface AuthorityItem {
    id: string;
    entity_name: string;
    type?: string;
    context?: string;
    proof_url?: string;
    logo_url?: string;
}

export interface TestimonialItem {
    id: string;
    type: "text" | "video";
    content: string;
    author_name: string;
    author_role?: string;
    author_avatar?: string;
    rating?: number;
}

export interface ContactData {
    support_email?: string;
    sales_email?: string;
    phone?: string;
    whatsapp?: string;
    address?: string;
    social_instagram?: string;
    social_linkedin?: string;
    social_youtube?: string;
    social_tiktok?: string;
    social_facebook?: string;
    social_twitter?: string;
    testimonials_url?: string;
}

export interface BrandVisuals {
    primary_color: string;
    accent_color: string;
    font_heading: string;
    font_body: string;
    style_preset?: string;
    
    // Brand Assets
    logos?: BrandLogos;

    // Extended Palette
    background_color?: string;
    text_primary_color?: string;
    text_on_primary?: string;
    
    // Context
    design_style?: string;
    usage_guidelines?: string[];
}

export interface BrandSettings {
    identity: BrandIdentity;
    story: BrandStory;
    strategy: BrandStrategy;
    visuals: BrandVisuals;
    team: KeyFigure[];
    testimonials: TestimonialItem[];
    authority_vault: AuthorityItem[];
    contact: ContactData;
}

export interface ExtractedVisuals {
    primary_color: string;
    accent_color: string;
    font_heading?: string;
    font_body?: string;
    
    // Extended Palette
    background_color: string;
    text_primary_color: string;
    text_on_primary: string;
    
    // Context
    design_style: string;
    usage_guidelines: string[];
}

export interface FullBrandExtractionRequest {
    url?: string;
    text?: string;
    mode: "initial" | "update";
    update_instructions?: string;
}

export const brandApi = {
    getBrandSettings: async (token: string): Promise<BrandSettings> => {
        const res = await fetchClient(`${API_URL}/api/v1/settings/brand`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        if (!res.ok) throw new Error("Failed to fetch brand settings");
        return res.json();
    },

    updateBrandSettings: async (data: BrandSettings, token: string): Promise<BrandSettings> => {
        const res = await fetchClient(`${API_URL}/api/v1/settings/brand`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to update brand settings");
        return res.json();
    },

    extractBrandVisuals: async (url: string, token: string): Promise<ExtractedVisuals> => {
        const res = await fetchClient(`${API_URL}/api/v1/tools/extract`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                url,
                type: "brand_identity"
            })
        });
        if (!res.ok) throw new Error("Failed to extract brand visuals");
        return res.json();
    },

    extractFullBrand: async (data: FullBrandExtractionRequest | FormData, token: string): Promise<BrandSettings> => {
        const isFormData = data instanceof FormData;
        
        const headers: HeadersInit = {
            Authorization: `Bearer ${token}`
        };

        if (!isFormData) {
            headers["Content-Type"] = "application/json";
        }

        // Ensure API_URL has a protocol
        let baseUrl = API_URL;
        if (baseUrl && !baseUrl.startsWith("http")) {
             // Fallback for relative URLs or missing protocol
             console.warn("API_URL missing protocol, defaulting to https://");
             baseUrl = `https://${baseUrl}`;
        }
        
        // Remove trailing slash if present to avoid double slashes
        if (baseUrl?.endsWith("/")) {
            baseUrl = baseUrl.slice(0, -1);
        }

        const url = `${baseUrl}/api/v1/tools/extract-full-brand`;
        console.log(`[BrandAPI] Extracting from: ${url}`);

        try {
            const res = await fetch(url, {
                method: "POST",
                headers,
                body: isFormData ? data : JSON.stringify(data)
            });

            if (!res.ok) {
                const errorText = await res.text();
                console.error(`[BrandAPI] Error ${res.status}: ${errorText}`);
                throw new Error(`Failed to extract full brand data: ${res.status} ${res.statusText}`);
            }
            return res.json();
        } catch (error) {
            console.error("[BrandAPI] Network or Fetch Error:", error);
            throw error;
        }
    }
};
