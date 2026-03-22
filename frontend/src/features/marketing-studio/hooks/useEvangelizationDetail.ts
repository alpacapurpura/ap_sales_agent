import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { EvangelizationDetail } from '../types/metrics';

export function useEvangelizationDetail() {
  const { getToken } = useAuth();
  const tenantId = typeof window !== 'undefined' ? localStorage.getItem('x-tenant-id') : null;

  return useQuery<EvangelizationDetail>({
    queryKey: ['evangelization-detail', tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getEvangelizationDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
