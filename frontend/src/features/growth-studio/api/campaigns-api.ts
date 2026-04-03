import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import type { CampaignOverview, AdSet, Ad } from '../types/campaigns';

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
