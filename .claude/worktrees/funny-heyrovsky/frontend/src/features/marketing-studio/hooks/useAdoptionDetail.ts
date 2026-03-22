import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { AdoptionDetail } from '../types/metrics';

export function useAdoptionDetail() {
  const { getToken, orgId } = useAuth();

  return useQuery<AdoptionDetail>({
    queryKey: ['adoption-detail', orgId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getAdoptionDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
