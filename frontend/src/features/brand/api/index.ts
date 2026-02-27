import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import { BrandSettings, ExtractedVisuals, FullBrandExtractionRequest } from "../types";
import { MOCK_BRAND_SETTINGS } from "./mock-data";
import { ENABLE_MOCKS as USE_MOCK_API } from "@/lib/mock-config";

const API_URL = config.api.baseUrl;

export const brandApi = {
    getBrandSettings: async (token: string): Promise<BrandSettings> => {
        if (USE_MOCK_API) {
            console.log("[BrandAPI] Using MOCK data for getBrandSettings");
            return new Promise((resolve) => setTimeout(() => resolve(MOCK_BRAND_SETTINGS), 800));
        }

        const res = await fetchClient(`${API_URL}/api/v1/settings/brand`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
        if (!res.ok) {
            const errorText = await res.text().catch(() => "Unknown error");
            console.error(`[BrandAPI] Failed to fetch settings: ${res.status} ${res.statusText}`, errorText);
            throw new Error(`Failed to fetch brand settings: ${res.status} ${res.statusText}`);
        }
        return res.json() as Promise<BrandSettings>;
    },

    updateBrandSettings: async (data: BrandSettings, token: string): Promise<BrandSettings> => {
        if (USE_MOCK_API) {
            console.log("[BrandAPI] Using MOCK data for updateBrandSettings", data);
            // Simulate merging updates into the mock (in a real app this would persist in memory or local storage)
            return new Promise((resolve) => setTimeout(() => resolve({ ...MOCK_BRAND_SETTINGS, ...data }), 600));
        }

        const res = await fetchClient(`${API_URL}/api/v1/settings/brand`, {
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
        return res.json() as Promise<ExtractedVisuals>;
    },

    extractFullBrand: async (data: FullBrandExtractionRequest | FormData, token: string): Promise<BrandSettings> => {
        let body: FormData;
        
        if (data instanceof FormData) {
            body = data;
        } else {
            // Convert plain object to FormData to satisfy FastAPI Form(...) dependency
            body = new FormData();
            if (data.url) body.append("url", data.url);
            if (data.text) body.append("text", data.text);
            if (data.mode) body.append("mode", data.mode);
            if (data.update_instructions) body.append("update_instructions", data.update_instructions);
        }
        
        const headers: HeadersInit = {
            Authorization: `Bearer ${token}`
        };
        // Do NOT set Content-Type for FormData, browser handles it

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

        // Create a controller to allow manual timeout (set to 8 minutes for full crawl + visuals)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 480000); // 8 minutes

        try {
            const res = await fetch(url, {
                method: "POST",
                headers,
                body: body,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!res.ok) {
                const errorText = await res.text();
                console.error(`[BrandAPI] Error ${res.status}: ${errorText}`);
                throw new Error(`Failed to extract full brand data: ${res.status} ${res.statusText}`);
            }
            return res.json();
        } catch (error: any) {
            clearTimeout(timeoutId);
            console.error("[BrandAPI] Network or Fetch Error:", error);
            if (error.name === 'AbortError') {
                throw new Error("La solicitud excedió el tiempo límite de 5 minutos.");
            }
            throw error;
        }
    }
};
