import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';

import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import type { CampaignOverview, AdSet, Ad } from '../types/campaigns';
import type { CampaignPerformanceData, MetaAdsPeriod } from '../types/metrics';

const API_URL = config.api.baseUrl;

export async function fetchCampaignOverview(token: string): Promise<CampaignOverview> {
  const res = await fetchClient(`${API_URL}/api/v1/analytics/campaigns`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Campaigns API returned ${res.status}`);
  return res.json();
}

export async function fetchCampaignAdSets(
  token: string,
  campaignExternalId: string,
): Promise<AdSet[]> {
  const res = await fetchClient(
    `${API_URL}/api/v1/analytics/campaigns/${campaignExternalId}/adsets`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok) throw new Error(`AdSets API returned ${res.status}`);
  return res.json();
}

export async function fetchAdSetAds(
  token: string,
  adSetExternalId: string,
): Promise<Ad[]> {
  const res = await fetchClient(
    `${API_URL}/api/v1/analytics/campaigns/adsets/${adSetExternalId}/ads`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!res.ok) throw new Error(`Ads API returned ${res.status}`);
  return res.json();
}

export async function triggerCampaignSync(token: string): Promise<{ status: string; job_id: string | null }> {
  const res = await fetchClient(`${API_URL}/api/v1/analytics/campaigns/sync`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Campaign sync trigger returned ${res.status}`);
  return res.json();
}

export async function fetchCampaignPerformance(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<CampaignPerformanceData> {
  const url = `${API_URL}/api/v1/analytics/campaigns/performance?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch campaign performance: ${res.status}`);
  }
  return res.json();
}

export function useCampaignPerformance(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['campaign-performance', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchCampaignPerformance(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 min
  });
}

// ── Demographics ──────────────────────────────────────────────────────

export interface DemographicSegment {
  label: string;
  value: number;
  percentage: number;
}

export interface DemographicsData {
  age: DemographicSegment[];
  gender: DemographicSegment[];
  placement: DemographicSegment[];
}

export async function fetchDemographics(
  token: string,
  channelSlug: string,
  period: MetaAdsPeriod = '30d',
): Promise<DemographicsData> {
  const url = `${API_URL}/api/v1/analytics/metrics/channel/${channelSlug}/demographics?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to fetch demographics: ${res.status}`);
  return res.json();
}

export function useDemographics(
  channelSlug: string,
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['demographics', channelSlug, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchDemographics(token, channelSlug, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

// ── Creatives ─────────────────────────────────────────────────────────

export interface AdPerformance {
  externalId: string;
  name: string;
  campaignName: string | null;
  campaignExternalId: string | null;
  status: string | null;
  effectiveStatus: string | null;
  creativeThumbnailUrl: string | null;
  creativeTitle: string | null;
  creativeCta: string | null;
  previewShareableLink: string | null;
}

export interface VideoRetention {
  plays: number;
  p25: number;
  p50: number;
  p75: number;
  p100: number;
}

export interface CreativesOverviewData {
  ads: AdPerformance[];
  videoRetention: VideoRetention;
  totalAds: number;
}

export async function fetchCreativesOverview(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<CreativesOverviewData> {
  const url = `${API_URL}/api/v1/analytics/campaigns/creatives?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Failed to fetch creatives: ${res.status}`);
  return res.json();
}

export function useCreativesOverview(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['creatives-overview', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchCreativesOverview(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}
