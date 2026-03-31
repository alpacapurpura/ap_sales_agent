import { useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { SyncAllResponse } from '../api/metrics-api';

export function useSyncAllSources() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (days: number = 30): Promise<SyncAllResponse> => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.triggerSyncAll(token, days);
    },
    onSuccess: () => {
      // Invalidate all stage queries so dashboards refresh
      queryClient.invalidateQueries({ queryKey: ['attraction-detail'] });
      queryClient.invalidateQueries({ queryKey: ['capture-detail'] });
      queryClient.invalidateQueries({ queryKey: ['nurture-detail'] });
      queryClient.invalidateQueries({ queryKey: ['opportunity-detail'] });
      queryClient.invalidateQueries({ queryKey: ['sales-detail'] });
      queryClient.invalidateQueries({ queryKey: ['adoption-detail'] });
      queryClient.invalidateQueries({ queryKey: ['expansion-detail'] });
      queryClient.invalidateQueries({ queryKey: ['evangelization-detail'] });
      queryClient.invalidateQueries({ queryKey: ['bowties-summary'] });
      queryClient.invalidateQueries({ queryKey: ['stage-timeseries'] });
    },
  });

  // Auto-reset result/error after 10s so button returns to "Sincronizar"
  useEffect(() => {
    if (!mutation.data && !mutation.error) return;
    const timer = setTimeout(() => mutation.reset(), 10_000);
    return () => clearTimeout(timer);
  }, [mutation.data, mutation.error]); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    trigger: mutation.mutate,
    isLoading: mutation.isPending,
    result: mutation.data,
    error: mutation.error,
    reset: mutation.reset,
  };
}
