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

/** Dynamic — accepts any channel slug from the backend. */
export type ChannelSlug = string;

export interface ChannelMetric {
  slug: string;
  name: string;
  channelType: string;
  value: number;
  cost?: number;
  sourceLabel: string;
  connected: boolean;
  costType?: string;
  unit?: string;
  currency?: string;
  lastUpdated?: string;
  badgeType?: string;
}

export interface TrafficGroup {
  totalValue: number;
  totalCost?: number;
  channels: ChannelMetric[];
}

export interface AvailableChannels {
  channels: ChannelMetric[];
}

export interface AttractionDetail {
  organic: TrafficGroup;
  paid: TrafficGroup & { totalCost: number };
  available?: AvailableChannels;
  period: string;
  lastUpdated?: string;
}
