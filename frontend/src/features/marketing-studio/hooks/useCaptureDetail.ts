import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { CaptureDetail } from '../types/metrics';

export function useCaptureDetail() {
  const { getToken } = useAuth();

  return useQuery<CaptureDetail>({
    queryKey: ['capture-detail'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getCaptureDetail(token);
    },
    staleTime: 1000 * 60 * 5,
  });
}
