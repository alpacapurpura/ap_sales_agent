import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import { aiActionsApi, ExtractionStatus } from "@/lib/api/ai-actions";
import { BrandSettings, BrandVisuals, FullBrandExtractionRequest } from "../types";
import { MOCK_BRAND_SETTINGS } from "./mock-data";
import { ENABLE_MOCKS as USE_MOCK_API } from "@/lib/mock-config";

const API_URL = config.api.baseUrl;

export const brandApi = {
    getBrandSettings: async (token: string): Promise<BrandSettings> => {
        if (USE_MOCK_API) {
            console.log("[BrandAPI] Using MOCK data for getBrandSettings");
            return new Promise((resolve) => setTimeout(() => resolve(MOCK_BRAND_SETTINGS), 800));
        }

        const res = await fetchClient(`${API_URL}/api/v1/brand/settings`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        
        if (!res.ok) {
            // Log error but attempt to return empty/default settings if 404
            // This prevents the entire UI from crashing for new users
            if (res.status === 404) {
                console.warn("[BrandAPI] Settings not found (404), returning empty object");
                return {} as BrandSettings;
            }

            const errorText = await res.text().catch(() => "Unknown error");
            console.error(`[BrandAPI] Failed to fetch settings: ${res.status} ${res.statusText}`, errorText);
            throw new Error(`Failed to fetch brand settings: ${res.status} ${res.statusText}`);
        }
        const data = await res.json() as BrandSettings;
        console.log("[BrandAPI] GET settings response:", {
            hasIdentity: !!data.identity?.brand_name,
            hasStory: !!(data.story as any)?.origin_story,
            hasStrategy: !!(data.strategy as any)?.value_proposition,
            teamCount: data.team?.length || 0,
            testimonialsCount: data.testimonials?.length || 0,
            authorityCount: data.authority_vault?.length || 0,
            keys: Object.keys(data),
        });
        return data;
    },

    updateBrandSettings: async (data: BrandSettings, token: string): Promise<BrandSettings> => {
        if (USE_MOCK_API) {
            console.log("[BrandAPI] Using MOCK data for updateBrandSettings", data);
            // Simulate merging updates into the mock (in a real app this would persist in memory or local storage)
            return new Promise((resolve) => setTimeout(() => resolve({ ...MOCK_BRAND_SETTINGS, ...data }), 600));
        }

        const res = await fetchClient(`${API_URL}/api/v1/brand/settings`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error("Failed to update brand settings");
        return res.json() as Promise<BrandSettings>;
    },

    extractBrandVisuals: async (url: string, token: string): Promise<BrandVisuals> => {
        const result = await aiActionsApi.extractBrandIdentity({
            url,
            type: "brand_identity"
        }, token);
        return result as BrandVisuals;
    },

    extractFullBrand: async (data: FullBrandExtractionRequest | FormData, token: string): Promise<{ job_id: string }> => {
        return aiActionsApi.extractFullBrand(data, token);
    },

    pollExtractionStatus: async (jobId: string, token: string): Promise<ExtractionStatus> => {
        return aiActionsApi.pollExtractionStatus(jobId, token);
    },
};
