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
