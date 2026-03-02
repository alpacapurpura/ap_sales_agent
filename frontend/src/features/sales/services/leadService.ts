import { fetchClient } from "@/lib/http-client";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Customer {
  id: string;
  full_name?: string;
  primary_email?: string;
  primary_phone?: string;
}

export interface Lead {
  id: string;
  customer_id?: string;
  customer?: Customer;
  fit_score: number;
  intent_score: number;
  temperature: string;
  created_at?: string;
  [key: string]: any;
}

export const leadService = {
  getLeads: async (query: string): Promise<Lead[]> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/crm/leads/search?q=${encodeURIComponent(query)}`);
    if (!res.ok) {
        throw new Error("Failed to fetch leads");
    }
    return res.json();
  },

  getLead: async (id: string): Promise<Lead> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/crm/leads/${id}`);
    if (!res.ok) {
        throw new Error("Failed to fetch lead");
    }
    return res.json();
  }
};
