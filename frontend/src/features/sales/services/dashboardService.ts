import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const BASE_URL = config.api.baseUrl;

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
    // TODO: implement when endpoints are ready
    return {
      total_sales: 0,
      appointments_today: 0,
      conversion_rate: 0,
      active_leads: 0,
    };
  },

  getActivity: async (): Promise<ActivityItem[]> => {
    // TODO: implement when endpoints are ready
    return [];
  },
};
