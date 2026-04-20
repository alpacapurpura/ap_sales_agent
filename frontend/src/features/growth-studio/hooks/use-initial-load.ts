import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { metricsApi } from "../api/metrics-api";

interface InitialLoadParams {
  provider: string;
  days?: number;
}

/**
 *
 */
export function useInitialLoad() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({ provider, days = 30 }: InitialLoadParams) => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return metricsApi.triggerInitialLoad(token, provider, days);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["attraction-detail"] });
      void queryClient.invalidateQueries({ queryKey: ["sales-detail"] });
      void queryClient.invalidateQueries({ queryKey: ["bowties-summary"] });
    },
  });

  // Auto-reset resultado/error después de 10s (patrón de useSyncAllSources)
  const mutationReset = mutation.reset;
  useEffect(() => {
    if (!mutation.data && !mutation.error) return;
    const timer = setTimeout(() => mutationReset(), 10_000);
    return () => clearTimeout(timer);
  }, [mutation.data, mutation.error, mutationReset]);

  return {
    trigger: mutation.mutate,
    isLoading: mutation.isPending,
    result: mutation.data,
    error: mutation.error,
    reset: mutation.reset,
  };
}
