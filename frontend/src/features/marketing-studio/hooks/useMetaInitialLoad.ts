import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';

export function useMetaInitialLoad() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (days: number = 30) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.triggerMetaInitialLoad(token, days);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attraction-detail'] });
    },
  });

  return {
    trigger: mutation.mutate,
    isLoading: mutation.isPending,
    result: mutation.data,
    error: mutation.error,
  };
}
