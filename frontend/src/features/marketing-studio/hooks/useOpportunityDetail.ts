import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { OpportunityDetail } from '../types/metrics';

export function useOpportunityDetail() {
  const { getToken } = useAuth();
  const tenantId = typeof window !== 'undefined' ? localStorage.getItem('x-tenant-id') : null;

  return useQuery<OpportunityDetail>({
    queryKey: ['opportunity-detail', tenantId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getOpportunityDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
