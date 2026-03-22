import { config } from "../config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface Lead {
    id: string;
    full_name: string;
    email: string;
    phone: string;
}

export const leadsApi = {
    search: async (q: string, token: string): Promise<Lead[]> => {
        const res = await fetchClient(`${API_URL}/api/v1/crm/leads/search?q=${encodeURIComponent(q)}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Error searching leads");
        return res.json();
    }
}
