export type StageId =
  | 'ATRACCION_CAPTURA' | 'ATRACCION' | 'CAPTURA' | 'NUTRICION_OPORTUNIDAD' | 'NUTRICION' | 'OPORTUNIDAD'
  | 'VENTAS' | 'ADOPCION' | 'EXPANSION_EVANGELIZACION' | 'EXPANSION' | 'EVANGELIZACION';

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
  /** All metrics associated with the channel, useful for detailed sidebars */
  channelMetrics?: MetricValue[];
  /** Optional channel name for display */
  channelName?: string;
  /** ISO 4217 currency code when the metric is a monetary value */
  currency?: string;
  lastUpdated?: Date;
  /** Extra data from headerKpis for enriched sidebar detail (e.g., sales breakdown) */
  extraData?: Record<string, number>;
  /** Sub-source breakdown for unified channels (e.g., Meta Direct + ManyChat) */
  subSources?: SubSource[];
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
  extra?: Record<string, unknown>;
}

export type GroupType = 'organic_social' | 'ga4_search' | 'paid' | 'outbound' | 'website' | 'web_infrastructure' | 'ai_agent' | 'retargeting' | 'automation' | 'checkout' | 'payment_links' | 'qualification' | 'adquisicion' | 'expansion' | 'available';

/** Sub-source breakdown for unified channels (e.g., Meta Direct + ManyChat) */
export interface SubSource {
  name: string;  // "Meta Direct", "ManyChat"
  leads: number;
  conversations: number;
}

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
  /** Display name of the specific property/channel/page the data comes from */
  sourceDisplayName?: string;
  /** Provider identifier (e.g., "google_analytics", "youtube", "meta") */
  providerName?: string;
  /** Sub-source breakdown when channel merges multiple providers */
  subSources?: SubSource[];
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
  website?: TrafficGroup;
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
  // Enriched Shopify metrics
  netSales: number;
  totalDiscounts: number;
  totalTax: number;
  refundCount: number;
  refundAmount: number;
  shippingRevenue: number;
  repeatCustomers: number;
  discountUsageCount: number;
  // Shopify aggregate KPIs (fallback display)
  shopifyRevenue: number;
  shopifyOrderCount: number;
  shopifyAvgOrderValue: number;
  shopifyCurrency: string;
}

export interface SalesDetail {
  headerKpis: SalesHeaderKpis;
  miniFunnel: MiniFunnelData;
  adquisicion: RevenueGroupData;
  expansion: RevenueGroupData;
  bottlenecks: BottleneckData[];
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

// ---------------------------------------------------------------------------
// Metric Catalog (semantic aggregation rules)
// ---------------------------------------------------------------------------

export type MetricAggregation = 'additive' | 'weighted_average' | 'derived' | 'non_aggregable' | 'snapshot';

export interface MetricCatalogEntry {
  name: string;
  display_name: string;
  description: string;
  interpretation: string;
  unit: string;
  aggregation: MetricAggregation;
  is_unique_metric: boolean;
  higher_is_better: boolean;
  providers: string[];
  weight_metric?: string;
  formula?: string;
  formula_components: string[];
  benchmarks?: string | null;
}

export interface MetricCatalog {
  metrics: MetricCatalogEntry[];
  count: number;
}

// ---------------------------------------------------------------------------
// Time Series (chart visualizations)
// ---------------------------------------------------------------------------

export interface TimeSeriesPoint {
  date: string;
  channels: Record<string, number>;
}

export interface ChannelInfo {
  slug: string;
  name: string;
  color: string;
}

export interface StageTimeSeries {
  stage: string;
  metricName: string;
  granularity: 'daily' | 'weekly';
  rangeDays: number;
  dataPoints: TimeSeriesPoint[];
  channelsPresent: ChannelInfo[];
  periodTotals: Record<string, number>;
  previousPeriodTotals: Record<string, number> | null;
}

// ---------------------------------------------------------------------------
// YouTube Analytics structured data
// ---------------------------------------------------------------------------

export interface YouTubeTrafficSource {
  insightTrafficSourceType: string;
  views: number;
  estimatedMinutesWatched: number;
}

export interface YouTubeTopVideo {
  videoId: string;
  title: string;
  thumbnailUrl: string;
  duration: string;
  publishedAt: string;
  views: number;
  likes: number;
  watchTimeMinutes: number;
  avgViewDuration: number;
}

export interface YouTubeDemographic {
  ageGroup: string;
  gender: string;
  viewerPercentage: number;
}

export interface YouTubeCountry {
  country: string;
  views: number;
  estimatedMinutesWatched: number;
}

// ---------------------------------------------------------------------------
// Channel Dashboard (Meta Ads deep-dive)
// ---------------------------------------------------------------------------

export type MetaAdsPeriod = '7d' | '30d' | '90d';

export interface BenchmarkRange {
  low: number;
  median: number;
  high: number;
  unit: string;
  interpretation: string;
}

export interface MetricKpiData {
  metricName: string;
  displayName: string;
  currentValue: number;
  previousValue: number | null;
  deltaPct: number | null;
  deltaAbsolute: number | null;
  unit: string;
  currency?: string;
  higherIsBetter: boolean;
  benchmark: BenchmarkRange | null;
}

export interface DashboardTimeSeriesPoint {
  date: string;
  value: number;
}

export interface MetricTimeSeries {
  metricName: string;
  displayName: string;
  unit: string;
  dataPoints: DashboardTimeSeriesPoint[];
}

export interface FunnelStep {
  label: string;
  metricName: string;
  value: number;
  conversionRate: number | null;
}

export interface FrequencyAlert {
  currentValue: number;
  severity: 'warning' | 'critical';
  message: string;
}

export interface ChannelDashboardData {
  channelSlug: string;
  channelName: string;
  industryCategory: string;
  period: string;
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
  funnel: { steps: FunnelStep[] };
  frequencyAlert: FrequencyAlert | null;
}

export type MetaAdsDashboardTab = 'resumen' | 'campanas' | 'creativos' | 'audiencia' | 'costos';

/** Generic alias -- usable by any channel dashboard */
export type ChannelDashboardPeriod = MetaAdsPeriod;

export type IgOrganicDashboardTab = 'overview' | 'contenido' | 'audiencia' | 'alcance';

export type YouTubeDashboardTab = 'overview' | 'videos' | 'audiencia' | 'engagement' | 'retencion';

export type MailDashboardTab = 'overview' | 'engagement' | 'entregabilidad' | 'lista' | 'automatizacion';

// ── Campaign Performance Types ──

export interface CampaignMetrics {
  spend: number;
  conversions: number;
  cpa: number | null;
  roas: number | null;
  ctr: number | null;
  cpc: number | null;
  cpm: number | null;
  frequency: number | null;
  impressions: number;
  clicks: number;
  reach: number;
}

export interface CampaignWithMetrics {
  externalId: string;
  name: string;
  objective: string | null;
  status: string | null;
  effectiveStatus: string | null;
  dailyBudget: number | null;
  lifetimeBudget: number | null;
  budgetRemaining: number | null;
  startTime: string | null;
  stopTime: string | null;
  adSetsCount: number;
  adsCount: number;
  metrics: CampaignMetrics;
  health: 'good' | 'warning' | 'critical';
}

export interface CampaignRecommendation {
  recommendationType: string;
  source: string;
  title: string | null;
  body: string | null;
  importance: string | null;
  liftEstimate: string | null;
  opportunityScore: number | null;
  url: string | null;
  objectIds: string[];
}

export interface CampaignPerformanceData {
  campaigns: CampaignWithMetrics[];
  recommendations: CampaignRecommendation[];
  totalCampaigns: number;
  activeCampaigns: number;
  currency: string | null;
  lastSynced: string | null;
}
