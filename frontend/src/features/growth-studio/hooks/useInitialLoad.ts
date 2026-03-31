import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';

interface InitialLoadParams {
  provider: string;
  days?: number;
}

export function useInitialLoad() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async ({ provider, days = 30 }: InitialLoadParams) => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.triggerInitialLoad(token, provider, days);
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
