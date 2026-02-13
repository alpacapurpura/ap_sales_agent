import { config } from "../config";
import { fetchClient } from "../http-client";
import { DashboardResponse } from "../../features/dashboard/types";

const API_URL = config.api.baseUrl;

export const dashboardApi = {
  getSummary: async (token: string): Promise<DashboardResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/dashboard/summary`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(`Error fetching dashboard summary: ${res.statusText}`);
    }

    return res.json();
  },
};
