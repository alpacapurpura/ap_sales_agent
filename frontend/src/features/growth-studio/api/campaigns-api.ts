import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';

import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { camelizeKeys } from '@/lib/case-conversion';
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
  // Backend returns snake_case (no alias_generator). The TypeScript type
  // CampaignPerformanceData expects camelCase, so we camelize the response
  // here. Skipping this caused campaign.externalId, effectiveStatus, etc.
  // to silently be `undefined` at runtime — surfaced as 422s when the
  // offer assignment drawer tried to POST target_external_id=undefined.
  const json: unknown = await res.json();
  return camelizeKeys<CampaignPerformanceData>(json);
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
  views30s: number;
  avgWatchTime: number;
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
  const json: unknown = await res.json();
  return camelizeKeys<CreativesOverviewData>(json);
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

// Shared camelizeKeys utility lives in @/lib/case-conversion.

// ── Ad-Level Performance ────────────────────────────────────────────

export interface AdMetrics {
  adId: string;
  adName: string;
  campaignName: string | null;
  campaignExternalId: string | null;
  formatType: string;
  thumbnailUrl: string | null;
  previewUrl: string | null;
  creativeBody: string | null;
  creativeCta: string | null;
  effectiveStatus: string | null;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  roas: number | null;
  cpa: number | null;
  ctr: number | null;
  cpc: number | null;
  performanceTag: string;
}

export interface AdPerformanceData {
  ads: AdMetrics[];
  period: string;
  totalAds: number;
  currency: string | null;
}

export interface FormatComparisonItem {
  formatType: string;
  emoji: string;
  adCount: number;
  avgCtr: number;
  avgCpa: number | null;
  avgRoas: number | null;
  totalSpend: number;
  performanceScore: number;
}

export interface FormatComparisonData {
  formats: FormatComparisonItem[];
  period: string;
  currency: string | null;
}

export async function fetchAdPerformance(
  token: string,
  period: MetaAdsPeriod = '30d',
  limit = 10,
): Promise<AdPerformanceData> {
  const url = `${API_URL}/api/v1/analytics/campaigns/ads/performance?period=${period}&limit=${limit}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Ad performance API returned ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<AdPerformanceData>(json);
}

export async function fetchFormatComparison(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<FormatComparisonData> {
  const url = `${API_URL}/api/v1/analytics/campaigns/ads/format-comparison?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Format comparison API returned ${res.status}`);
  const json: unknown = await res.json();
  return camelizeKeys<FormatComparisonData>(json);
}

export function useAdPerformance(
  period: MetaAdsPeriod = '30d',
  limit = 10,
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['ad-performance', period, limit],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchAdPerformance(token, period, limit);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useFormatComparison(
  period: MetaAdsPeriod = '30d',
  enabled = true,
) {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ['format-comparison', period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return fetchFormatComparison(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}
