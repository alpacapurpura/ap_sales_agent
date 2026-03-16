import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { NurtureDetail } from '../types/metrics';

export function useNurtureDetail() {
  const { getToken } = useAuth();

  return useQuery<NurtureDetail>({
    queryKey: ['nurture-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getNurtureDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
