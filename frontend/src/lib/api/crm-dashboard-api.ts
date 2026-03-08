import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

export interface PipelineItem {
    id: string;
    full_name: string | null;
    intent_score: number;
    temperature: string;
    last_interaction: string | null;
    channel: string | null;
    avatar_url?: string | null;
}

export interface AgendaItem {
    id: string;
    summary: string;
    start_time: string;
    end_time: string;
    status: string;
    lead_name?: string | null;
    meeting_link?: string | null;
}

export interface TickerItem {
    id: string;
    amount: number;
    currency: string;
    customer_name?: string | null;
    stage: string;
    occurred_at: string;
    offer_name?: string | null;
}

export const crmDashboardApi = {
    getPipeline: async (token: string, minScore: number = 50, limit: number = 20): Promise<PipelineItem[]> => {
        const res = await fetchClient(`${API_URL}/api/v1/crm/pipeline/pipeline?min_score=${minScore}&limit=${limit}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Error fetching pipeline");
        return res.json();
    },

    getAgenda: async (token: string, range: "today" | "week" = "today"): Promise<AgendaItem[]> => {
        const res = await fetchClient(`${API_URL}/api/v1/scheduling/agenda/?range=${range}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Error fetching agenda");
        return res.json();
    },

    getTicker: async (token: string, range: "today" | "week" | "30d" | "all" = "30d"): Promise<TickerItem[]> => {
        const res = await fetchClient(`${API_URL}/api/v1/crm/sales/ticker?range=${range}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!res.ok) throw new Error("Error fetching ticker");
        return res.json();
    }
};
