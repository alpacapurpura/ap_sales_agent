import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { ExpansionDetailData } from '../types/metrics';

export function useExpansionDetail() {
  const { getToken, orgId } = useAuth();

  return useQuery<ExpansionDetailData>({
    queryKey: ['expansion-detail', orgId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getExpansionDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
