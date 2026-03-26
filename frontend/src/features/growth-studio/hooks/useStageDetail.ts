import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { AttractionDetail, CaptureDetail, NurtureDetail, OpportunityDetail, SalesDetail, AdoptionDetail, ExpansionDetailData, EvangelizationDetail } from '../types/metrics';

function createStageDetailHook<T>(
  queryKey: string,
  apiFn: (token: string) => Promise<T>
) {
  return function useStageDetail() {
    const { getToken } = useAuth();
    const tenantId = typeof window !== 'undefined'
      ? localStorage.getItem('x-tenant-id') : null;

    return useQuery<T>({
      queryKey: [queryKey, tenantId],
      queryFn: async () => {
        const token = await getToken();
        if (!token) throw new Error('No auth token');
        return apiFn(token);
      },
      staleTime: 1000 * 60 * 5,
    });
  };
}

export const useAttractionDetail = createStageDetailHook<AttractionDetail>('attraction-detail', metricsApi.getAttractionDetail);
export const useCaptureDetail = createStageDetailHook<CaptureDetail>('capture-detail', metricsApi.getCaptureDetail);
export const useNurtureDetail = createStageDetailHook<NurtureDetail>('nurture-detail', metricsApi.getNurtureDetail);
export const useOpportunityDetail = createStageDetailHook<OpportunityDetail>('opportunity-detail', metricsApi.getOpportunityDetail);
export const useSalesDetail = createStageDetailHook<SalesDetail>('sales-detail', metricsApi.getSalesDetail);
export const useAdoptionDetail = createStageDetailHook<AdoptionDetail>('adoption-detail', metricsApi.getAdoptionDetail);
export const useExpansionDetail = createStageDetailHook<ExpansionDetailData>('expansion-detail', metricsApi.getExpansionDetail);
export const useEvangelizationDetail = createStageDetailHook<EvangelizationDetail>('evangelization-detail', metricsApi.getEvangelizationDetail);
