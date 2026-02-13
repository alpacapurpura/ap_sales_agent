import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { dashboardApi } from "../../../lib/api/dashboard";
import { DashboardResponse } from "../types";

export const useDashboardSummary = () => {
  const { getToken, isLoaded, isSignedIn } = useAuth();

  return useQuery<DashboardResponse>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return dashboardApi.getSummary(token);
    },
    enabled: isLoaded && isSignedIn,
    staleTime: 1000 * 60, // 1 minute
    refetchOnWindowFocus: true,
  });
};
