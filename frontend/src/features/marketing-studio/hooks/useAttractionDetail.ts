import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { AttractionDetail } from '../types/metrics';

export function useAttractionDetail() {
  const { getToken, orgId } = useAuth();

  return useQuery<AttractionDetail>({
    queryKey: ['attraction-detail', orgId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getAttractionDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
