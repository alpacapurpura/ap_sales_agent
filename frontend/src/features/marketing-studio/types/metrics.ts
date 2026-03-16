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

/** Dynamic -- accepts any channel slug from the backend. */
export type ChannelSlug = string;

/** Single named metric within a channel (e.g., reach, engagement, spend). */
export interface MetricValue {
  name: string;
  value: number;
  unit?: string;
  currency?: string;
  breakdown?: Record<string, number>;
}

export type GroupType = 'organic_social' | 'ga4_search' | 'paid' | 'outbound' | 'web_infrastructure' | 'ai_agent' | 'available';

export interface ChannelMetric {
  slug: string;
  name: string;
  channelType: string;
  metrics: MetricValue[];
  sourceLabel: string;
  connected: boolean;
  costType?: string;
  lastUpdated?: string;
  stale?: boolean;
  errorMessage?: string;
  /** @deprecated use metrics array instead */
  value?: number;
}

export interface TrafficGroup {
  totals: Record<string, number>;
  channels: ChannelMetric[];
}

export interface AvailableChannels {
  channels: ChannelMetric[];
}

export interface AttractionDetail {
  organicSocial: TrafficGroup;
  ga4Search: TrafficGroup;
  paid: TrafficGroup;
  outbound: TrafficGroup;
  available?: AvailableChannels;
  period: string;
  lastUpdated?: string;
}

// === Capture (Stage 1) Types ===

export type CaptureGroupType = 'web_infrastructure' | 'ai_agent' | 'available';

export interface CaptureHeaderKpis {
  totalLeads: number;
  conversionRate: number; // percentage 0-100
  costPerLead: number | null; // null = unconfigured
}

export interface MiniFunnelData {
  sourceLabel: string;  // "Visitantes"
  sourceValue: number;
  targetLabel: string;  // "Leads"
  targetValue: number;
  conversionRate: number; // percentage
}

export interface CaptureDetail {
  headerKpis: CaptureHeaderKpis;
  miniFunnel: MiniFunnelData;
  webInfrastructure: TrafficGroup;
  aiAgent: TrafficGroup;
  available?: AvailableChannels;
  period: string;
  lastUpdated?: string;
}
