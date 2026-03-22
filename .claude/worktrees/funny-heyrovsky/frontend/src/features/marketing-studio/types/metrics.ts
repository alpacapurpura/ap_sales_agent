export type StageId =
  | 'ATRACCION' | 'CAPTURA' | 'NUTRICION' | 'OPORTUNIDAD'
  | 'VENTAS' | 'ADOPCION' | 'EXPANSION' | 'EVANGELIZACION';

/**
 * Single KPI header entry used in the 3-KPI header row of every detail panel.
 * value can be numeric or a pre-formatted string (e.g., dual-currency like "$4,200 (~$220 USD)").
 */
export interface HeaderKpiData {
  label: string;
  value: number | string;
  unit?: string;
  /** Plain-Spanish tooltip hint shown on hover (see KpiTooltip component) */
  tooltip?: string;
  /** When true, renders skeleton shimmer instead of the value */
  isLoading?: boolean;
}

/**
 * Data passed when a metric in a detail panel is clicked to open the action sidebar.
 * Created in Plan 11-01 Task 3 (MetricSidebar framework); content adapters added in Plan 11-02.
 */
export interface MetricClickData {
  stageId: StageId;
  channelSlug: string;
  /** Human-readable metric name, e.g. "visitors", "leads", "impressions" */
  metricName: string;
  currentValue: number;
  /** ISO 4217 currency code when the metric is a monetary value */
  currency?: string;
  lastUpdated?: Date;
}

export interface StageSummary {
  id: StageId;
  order: number;
  label: string;
  description: string;
  /**
   * Primary KPI shown large in the StageCard (top row).
   * Maps to the most important metric per stage:
   *   ATRACCION=visitors, CAPTURA=leads, NUTRICION=MQLs, OPORTUNIDAD=SQLs,
   *   VENTAS=revenue, ADOPCION=healthPct, EXPANSION=netMrr, EVANGELIZACION=kFactor
   */
  mainKpi: { label: string; value: number | string; unit?: string };
  /**
   * Secondary KPI shown below mainKpi as small muted text.
   * For stages 1-7: conversion rate from previous stage ("X.X% conversion").
   * For stage 0 (ATRACCION): total spend or channels active count (no conversion rate).
   */
  secondaryKpi: { label: string; value: number | string; unit?: string };
  hasDetail: boolean;
  /**
   * Optional array of 3 primary KPIs for detail panel header (from API response headerKpis).
   * When undefined, detail panels derive their own KPIs from the stage-specific API shape.
   */
  headerKpis?: HeaderKpiData[];
  /**
   * Mini-funnel conversion rate from previous stage to this one (percentage 0-100).
   * Used as secondaryKpi when available.
   */
  miniFunnelConversionRate?: number;
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

// === Stage 7: Evangelizacion ===

export interface EvangelizationHeaderKpis {
  kFactor: number;           // X.XX
  referralConversions: number;
  npsScore: number | null;   // 0-10 scale, null if no data
  referralRevenue: number;
  referralRevenueUsd: number | null;
  currency: string;
  activeEvangelists: number;
}

export interface EvangelistData {
  customerId: string;
  fullName: string;
  referralCode: string;
  referralsSent: number;
  conversions: number;
  revenueAttributed: number;
  currency: string;
  usdRevenue: number | null;
  isActive: boolean;
}

export interface CandidatoData {
  customerId: string;
  fullName: string;
  npsScore: number;          // 0-10
  respondedAt: string | null;
}

export interface NpsSummaryData {
  npsScore: number | null;   // 0-10 average
  standardNps: number | null; // -100 to +100
  promoterCount: number;
  passiveCount: number;
  detractorCount: number;
  totalResponses: number;
  surveysSent: number;
  responseRatePct: number;
}

export interface EvangelizationBottleneck {
  type: string;
  metricLabel: string;
  currentRate: number;
  severity: 'normal' | 'warning' | 'critical';
  threshold: number;
  tip: string;
}

export interface EvangelizationDetail {
  headerKpis: EvangelizationHeaderKpis;
  miniFunnel: MiniFunnelData;
  referidos: EvangelistData[];
  candidatos: CandidatoData[];
  npsSummary: NpsSummaryData;
  ugcCount: number;
  ugcWritten: number;
  ugcAudio: number;
  bottlenecks: EvangelizationBottleneck[];
  period: string;
  lastUpdated?: string;
}
