import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { SalesDetail } from '../types/metrics';

export function useSalesDetail() {
  const { getToken, orgId } = useAuth();

  return useQuery<SalesDetail>({
    queryKey: ['sales-detail', orgId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getSalesDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
