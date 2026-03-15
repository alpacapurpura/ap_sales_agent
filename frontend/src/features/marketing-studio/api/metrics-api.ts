import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { ENABLE_MOCKS } from '@/lib/mock-config';
import type { AttractionDetail, ChannelMetric, MetricValue } from '../types/metrics';
import { MOCK_ATTRACTION_DETAIL } from './metrics-mock-data';

const API_URL = config.api.baseUrl;

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapMetric(raw: any): MetricValue {
  return {
    name: raw.name,
    value: raw.value,
    unit: raw.unit ?? undefined,
    currency: raw.currency ?? undefined,
    breakdown: raw.breakdown ?? undefined,
  };
}

function mapChannel(raw: any): ChannelMetric {
  return {
    slug: raw.slug,
    name: raw.name,
    channelType: raw.channel_type,
    metrics: (raw.metrics ?? []).map(mapMetric),
    sourceLabel: raw.source_label,
    connected: raw.connected,
    costType: raw.cost_type ?? undefined,
    lastUpdated: raw.last_updated ?? undefined,
    stale: raw.stale ?? false,
    errorMessage: raw.error_message ?? undefined,
    value: raw.value ?? undefined,
  };
}

function mapGroup(raw: any) {
  return {
    totals: raw.totals ?? {},
    channels: (raw.channels ?? []).map(mapChannel),
  };
}

function mapResponse(raw: any): AttractionDetail {
  return {
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
    organicSocial: mapGroup(raw.organic_social),
    ga4Search: mapGroup(raw.ga4_search),
    paid: mapGroup(raw.paid),
    outbound: mapGroup(raw.outbound),
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

export const metricsApi = {
  getAttractionDetail: async (token: string): Promise<AttractionDetail> => {
    if (ENABLE_MOCKS) {
      return MOCK_ATTRACTION_DETAIL;
    }

    try {
      const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/attraction`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.warn('Attraction API returned', res.status, '-- using mock data');
        return MOCK_ATTRACTION_DETAIL;
      }

      const data = await res.json();
      return mapResponse(data);
    } catch (error) {
      console.warn('Attraction API error -- using mock data:', error);
      return MOCK_ATTRACTION_DETAIL;
    }
  },
};
