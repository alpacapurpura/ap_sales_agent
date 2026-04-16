import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { metricsApi } from "../api/metrics-api";
import { useGrowthStudioContext } from "../components/metrics-dashboard/context/GrowthStudioContext";

import type { PeriodType } from "../api/stage-detail-api";
import type {
  AttractionDetail,
  CaptureDetail,
  NurtureDetail,
  OpportunityDetail,
  SalesDetail,
  AdoptionDetail,
  ExpansionDetailData,
  EvangelizationDetail,
  StageTimeSeries,
} from "../types/metrics";

interface StageDetailHookOptions {
  /** When false, the query will not execute. Defaults to true. */
  enabled?: boolean;
}

function createStageDetailHook<T>(
  queryKey: string,
  apiFn: (token: string, period?: PeriodType) => Promise<T>,
) {
  return function useStageDetail(options?: StageDetailHookOptions) {
    const { getToken } = useAuth();
    const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;
    const { selectedPeriod } = useGrowthStudioContext();

    return useQuery<T>({
      queryKey: [queryKey, tenantId, selectedPeriod],
      queryFn: async () => {
        const token = await getToken();
        if (!token) throw new Error("No auth token");
        return apiFn(token, selectedPeriod);
      },
      staleTime: 1000 * 60 * 5,
      enabled: options?.enabled ?? true,
    });
  };
}

export const useAttractionDetail = createStageDetailHook<AttractionDetail>(
  "attraction-detail",
  metricsApi.getAttractionDetail,
);
export const useCaptureDetail = createStageDetailHook<CaptureDetail>(
  "capture-detail",
  metricsApi.getCaptureDetail,
);
export const useNurtureDetail = createStageDetailHook<NurtureDetail>(
  "nurture-detail",
  metricsApi.getNurtureDetail,
);
export const useOpportunityDetail = createStageDetailHook<OpportunityDetail>(
  "opportunity-detail",
  metricsApi.getOpportunityDetail,
);
export const useSalesDetail = createStageDetailHook<SalesDetail>(
  "sales-detail",
  metricsApi.getSalesDetail,
);
export const useAdoptionDetail = createStageDetailHook<AdoptionDetail>(
  "adoption-detail",
  metricsApi.getAdoptionDetail,
);
export const useExpansionDetail = createStageDetailHook<ExpansionDetailData>(
  "expansion-detail",
  metricsApi.getExpansionDetail,
);
export const useEvangelizationDetail = createStageDetailHook<EvangelizationDetail>(
  "evangelization-detail",
  metricsApi.getEvangelizationDetail,
);

// eslint-disable-next-line max-params -- hook mirrors API signature; options object would complicate React Query key
export function useStageTimeSeries(
  stage: string,
  metric: string,
  rangeDays: number,
  granularity: string,
  options?: { enabled?: boolean },
) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<StageTimeSeries>({
    queryKey: ["stage-timeseries", tenantId, stage, metric, rangeDays, granularity],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return metricsApi.getTimeSeries(token, stage, metric, rangeDays, granularity);
    },
    staleTime: 1000 * 60 * 5,
    enabled: options?.enabled ?? true,
  });
}
