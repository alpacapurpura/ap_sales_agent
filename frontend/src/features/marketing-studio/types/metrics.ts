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

export type GroupType = 'organic_social' | 'ga4_search' | 'paid' | 'outbound' | 'web_infrastructure' | 'ai_agent' | 'retargeting' | 'automation' | 'checkout' | 'payment_links' | 'qualification' | 'adquisicion' | 'expansion' | 'available';

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

// === Nurture (Stage 2) Types ===

export type NurtureGroupType = 'retargeting' | 'automation' | 'available';

export interface NurtureHeaderKpis {
  totalMqls: number;
  conversionRate: number; // percentage 0-100
  costPerMql: number | null; // null = unconfigured
}

export interface CampaignMetric {
  campaignName: string;
  campaignId?: string;
  metrics: MetricValue[];
}

export interface NurtureDetail {
  headerKpis: NurtureHeaderKpis;
  miniFunnel: MiniFunnelData;
  retargeting: TrafficGroup;
  automation: TrafficGroup;
  available?: AvailableChannels;
  period: string;
  lastUpdated?: string;
}

// === Opportunity (Stage 3) Types ===

export type OpportunityGroupType = 'checkout' | 'payment_links' | 'qualification' | 'available';

export interface OpportunityHeaderKpis {
  totalSqls: number;
  conversionRate: number;        // percentage 0-100 (MQL -> SQL)
  costPerSql: number | null;     // null = unconfigured
}

export interface BottleneckData {
  type: 'abandoned_cart' | 'meeting_no_show';
  metricLabel: string;
  currentRate: number;           // percentage 0-100
  severity: 'normal' | 'warning' | 'critical';
  threshold: number;
  tip: string;
}

export interface OpportunityDetail {
  headerKpis: OpportunityHeaderKpis;
  miniFunnel: MiniFunnelData;    // reuse existing type
  checkout: TrafficGroup;
  paymentLinks: TrafficGroup;
  qualification: TrafficGroup;
  bottlenecks: BottleneckData[];
  available?: AvailableChannels;
  period: string;
  lastUpdated?: string;
}

// === Stage 4: Ventas (Sales) ===

export interface OfferSaleData {
  offerId: string;
  publicName: string;
  offerType: string;
  pricingType: 'one_time' | 'subscription' | 'payment_plan';
  totalRevenue: number;
  salesCount: number;
  currency: string;
  usdRevenue: number | null;
  sourceBreakdown: Record<string, number>;
  newSubscriptions: number | null;
  newSubscriptionRevenue: number | null;
  renewals: number | null;
  renewalRevenue: number | null;
  subscriptionNewLabel: string | null;
  subscriptionRenewalLabel: string | null;
}

export interface TierGroupData {
  tierKey: string;
  tierLabel: string;
  offers: OfferSaleData[];
}

export interface RevenueGroupData {
  groupKey: 'adquisicion' | 'expansion';
  groupLabel: string;
  totalRevenue: number;
  totalRevenueUsd: number | null;
  customerCount: number;
  revenuePercentage: number;
  currency: string;
  tiers: TierGroupData[];
}

export interface SalesHeaderKpis {
  totalRevenue: number;
  totalRevenueUsd: number | null;
  currency: string;
  newCustomers: number;
  cac: number | null;
  cacIncomplete: boolean;
}

export interface SalesBottleneck {
  type: string;
  severity: 'warning' | 'critical';
  message: string;
  tip: string;
}

export interface SalesDetail {
  headerKpis: SalesHeaderKpis;
  miniFunnel: MiniFunnelData;
  adquisicion: RevenueGroupData;
  expansion: RevenueGroupData;
  bottlenecks: SalesBottleneck[];
  period: string;
  lastUpdated?: string;
}

// === Stage 5: Adopcion ===

export interface OfferHealthData {
  offerId: string;
  publicName: string;
  totalCustomers: number;
  activeCount: number;
  inactiveCount: number;
  healthPct: number;
  ttvDays: number | null;
}

export interface AdoptionHeaderKpis {
  activeCustomers: number;
  inactiveCustomers: number;
  healthPct: number;
  avgTtvDays: number | null;
  refundCount: number;
  refundAmount: number;
  refundCurrency: string;
  refundAmountUsd: number | null;
}

export interface AdoptionBottleneck {
  type: string;
  metricLabel: string;
  currentRate: number;
  severity: 'normal' | 'warning' | 'critical';
  threshold: number;
  tip: string;
}

export interface AdoptionDetail {
  headerKpis: AdoptionHeaderKpis;
  miniFunnel: MiniFunnelData;
  offers: OfferHealthData[];
  bottlenecks: AdoptionBottleneck[];
  period: string;
  lastUpdated?: string;
}

// === Stage 6: Expansion ===

export interface ExpansionOfferData {
  offerId: string;
  publicName: string;
  count: number;
  revenue: number;
  currency: string;
  usdRevenue: number | null;
}

export interface ExpansionGroupData {
  groupKey: 'retencion' | 'crecimiento' | 'cancelaciones';
  groupLabel: string;
  groupSubtitle: string;
  totalCount: number;
  totalRevenue: number;
  totalRevenueUsd: number | null;
  currency: string;
  ratePct: number | null;
  offers: ExpansionOfferData[];
}

export interface ExpansionHeaderKpis {
  netMrr: number;
  netMrrUsd: number | null;
  currency: string;
  avgLtv: number;
  avgLtvUsd: number | null;
  churnRatePct: number;
}

export interface ExpansionBottleneck {
  type: string;
  metricLabel: string;
  currentRate: number;
  severity: 'normal' | 'warning' | 'critical';
  threshold: number;
  tip: string;
}

export interface ExpansionDetailData {
  headerKpis: ExpansionHeaderKpis;
  miniFunnel: MiniFunnelData;
  retencion: ExpansionGroupData;
  crecimiento: ExpansionGroupData;
  cancelaciones: ExpansionGroupData;
  bottlenecks: ExpansionBottleneck[];
  period: string;
  lastUpdated?: string;
}
