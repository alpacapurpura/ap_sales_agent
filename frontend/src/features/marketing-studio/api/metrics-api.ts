import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { ENABLE_MOCKS } from '@/lib/mock-config';
import type { AttractionDetail, ChannelMetric } from '../types/metrics';
import { MOCK_ATTRACTION_DETAIL } from './metrics-mock-data';

const API_URL = config.api.baseUrl;

/* eslint-disable @typescript-eslint/no-explicit-any */
function mapChannel(raw: any): ChannelMetric {
  return {
    slug: raw.slug,
    name: raw.name,
    channelType: raw.channel_type,
    value: raw.value,
    cost: raw.cost ?? undefined,
    sourceLabel: raw.source_label,
    connected: raw.connected,
  };
}

function mapResponse(raw: any): AttractionDetail {
  return {
    period: raw.period,
    organic: {
      totalValue: raw.organic.total_value,
      channels: raw.organic.channels.map(mapChannel),
    },
    paid: {
      totalValue: raw.paid.total_value,
      totalCost: raw.paid.total_cost,
      channels: raw.paid.channels.map(mapChannel),
    },
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
        console.warn('Attraction API returned', res.status, '— using mock data');
        return MOCK_ATTRACTION_DETAIL;
      }

      const data = await res.json();
      return mapResponse(data);
    } catch (error) {
      console.warn('Attraction API error — using mock data:', error);
      return MOCK_ATTRACTION_DETAIL;
    }
  },
};
