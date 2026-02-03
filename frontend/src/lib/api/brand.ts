import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface BrandIdentity {
    brand_name?: string;
    legal_name?: string;
    website?: string;
    industry?: string;
    logo_url?: string;
    timezone?: string;
    language?: string;
}

export interface KeyFigure {
    id: string;
    name: string;
    role?: string;
    is_primary_voice: boolean;
    bio?: string;
    gender?: "Masculino" | "Femenino" | "Neutro";
    communication_style?: string;
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

export interface ContactData {
    support_email?: string;
    phone?: string;
    address?: string;
    social_instagram?: string;
    social_linkedin?: string;
    social_youtube?: string;
    testimonials_url?: string;
}

export interface BrandSettings {
    identity: BrandIdentity;
    team: KeyFigure[];
    authority_vault: AuthorityItem[];
    contact: ContactData;
}

export const brandApi = {
    getBrandSettings: async (token: string): Promise<BrandSettings> => {
        const res = await fetch(`${API_URL}/api/v1/settings/brand`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        if (!res.ok) throw new Error("Failed to fetch brand settings");
        return res.json();
    },

    updateBrandSettings: async (data: BrandSettings, token: string): Promise<BrandSettings> => {
        const res = await fetch(`${API_URL}/api/v1/settings/brand`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to update brand settings");
        return res.json();
    }
};
