import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { SalesDetail } from '../types/metrics';

export function useSalesDetail() {
  const { getToken } = useAuth();
  const tenantId = typeof window !== 'undefined' ? localStorage.getItem('x-tenant-id') : null;

  return useQuery<SalesDetail>({
    queryKey: ['sales-detail', tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getSalesDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
