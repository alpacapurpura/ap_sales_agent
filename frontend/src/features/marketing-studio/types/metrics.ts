export type StageId =
  | 'ATRACCION' | 'CAPTURA' | 'NUTRICION' | 'OPORTUNIDAD'
  | 'VENTAS' | 'ADOPCION' | 'EXPANSION' | 'EVANGELIZACION';

export interface StageSummary {
  id: StageId;
  order: number;
  label: string;
  description: string;
  mainKpi: { label: string; value: number; unit?: string };
  secondaryKpi: { label: string; value: number; unit?: string };
  hasDetail: boolean;
}

export type ChannelSlug =
  | 'ig-organic' | 'yt-organic' | 'fb-organic' | 'tiktok-organic'
  | 'linkedin-organic' | 'google-organic' | 'direct' | 'ai-search-organic'
  | 'meta-ads' | 'tiktok-ads' | 'google-ads' | 'yt-ads' | 'cold-contact';

export interface ChannelMetric {
  slug: ChannelSlug;
  name: string;
  channelType: 'ORGANIC_SOCIAL' | 'ORGANIC_SEARCH' | 'PAID_MEDIA';
  value: number;
  cost?: number;
  sourceLabel: string;
  connected: boolean;
}

export interface TrafficGroup {
  totalValue: number;
  totalCost?: number;
  channels: ChannelMetric[];
}

export interface AttractionDetail {
  organic: TrafficGroup;
  paid: TrafficGroup & { totalCost: number };
  period: string;
}
