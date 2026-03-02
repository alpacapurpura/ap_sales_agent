import { fetchClient } from "@/lib/http-client";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface DashboardStats {
  total_sales: number;
  appointments_today: number;
  conversion_rate: number;
  active_leads: number;
}

export interface ActivityItem {
  id: string;
  type: "lead" | "appointment" | "payment" | "alert";
  title: string;
  description: string;
  timestamp: string;
  amount?: number;
}

export const dashboardService = {
  getStats: async (): Promise<DashboardStats> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/sales-agent/dashboard/stats`);
    if (!res.ok) {
        throw new Error("Failed to fetch dashboard stats");
    }
    return res.json();
  },

  getActivity: async (): Promise<ActivityItem[]> => {
    const res = await fetchClient(`${BASE_URL}/api/v1/sales-agent/dashboard/activity`);
    if (!res.ok) {
        throw new Error("Failed to fetch dashboard activity");
    }
    return res.json();
  }
};
