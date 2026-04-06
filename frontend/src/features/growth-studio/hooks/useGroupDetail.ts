'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import { useGrowthStudioContext } from '../components/metrics-dashboard/context/GrowthStudioContext';
import type { TrafficGroup } from '../types/metrics';

interface GroupDetailData {
  channels: TrafficGroup['channels'];
  totals: TrafficGroup['totals'];
}

interface UseGroupDetailOptions {
  /** When false, the query will not execute. Defaults to false (load on demand). */
  enabled?: boolean;
}

/**
 * Maps stage names to their API method names for fetching detail data.
 */
const STAGE_API_MAP: Record<string, keyof typeof metricsApi> = {
  attraction: 'getAttractionDetail',
  capture: 'getCaptureDetail',
  nurturing: 'getNurtureDetail',
  opportunity: 'getOpportunityDetail',
  sales: 'getSalesDetail',
  adoption: 'getAdoptionDetail',
  expansion: 'getExpansionDetail',
  evangelization: 'getEvangelizationDetail',
};

/**
 * Fetches detail data for a specific group within a stage (Tier 2).
 *
 * Loads ONLY when `enabled=true` — intended to be triggered by IntersectionObserver
 * when the group's ChannelGroup enters the viewport.
 *
 * Uses the existing full stage detail endpoint with a groups filter param
 * (or falls back to fetching full and extracting the group client-side).
 */
export function useGroupDetail(stage: string, groupKey: string, options?: UseGroupDetailOptions) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== 'undefined'
    ? localStorage.getItem('x-tenant-id') : null;
  const { selectedPeriod } = useGrowthStudioContext();

  return useQuery<GroupDetailData | undefined>({
    queryKey: ['stage-group-detail', tenantId, stage, groupKey, selectedPeriod],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');

      const apiFn = STAGE_API_MAP[stage];
      if (!apiFn) return undefined;

      // Call the full stage detail API (will benefit from React Query cache if already loaded)
      // The backend supports ?groups= filter when available, but we extract client-side for now
      const fullData = await (metricsApi[apiFn] as (token: string, period?: string) => Promise<Record<string, unknown>>)(token, selectedPeriod);

      // Extract the specific group from the response
      return extractGroup(fullData, groupKey);
    },
    staleTime: 1000 * 60 * 5,
    enabled: options?.enabled ?? false,
  });
}

/**
 * Extracts a specific traffic group from a stage detail response.
 * The field names vary per stage, so we map groupKey to the response field.
 */
function extractGroup(data: Record<string, unknown>, groupKey: string): GroupDetailData | undefined {
  // Direct field mapping: group keys correspond to camelCase field names in the DTO
  const fieldMap: Record<string, string> = {
    organic_social: 'organicSocial',
    ga4_search: 'ga4Search',
    paid: 'paid',
    outbound: 'outbound',
    website: 'website',
    web_infrastructure: 'webInfrastructure',
    ai_agent: 'aiAgent',
    retargeting: 'retargeting',
    automation: 'automation',
    checkout: 'checkout',
    payment_links: 'paymentLinks',
    qualification: 'qualification',
    adquisicion: 'adquisicion',
    expansion: 'expansion',
    retencion: 'retencion',
    crecimiento: 'crecimiento',
    cancelaciones: 'cancelaciones',
  };

  const fieldName = fieldMap[groupKey];
  if (!fieldName) return undefined;

  const group = data[fieldName] as { channels?: unknown[]; totals?: Record<string, number> } | undefined;
  if (!group) return undefined;

  return {
    channels: (group.channels ?? []) as GroupDetailData['channels'],
    totals: (group.totals ?? {}) as GroupDetailData['totals'],
  };
}
