import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import { ENABLE_MOCKS } from "@/lib/mock-config";

import { mapChannel, mapGroup } from "./mappers/shared";

import type { RawGroup, RawChannel } from "./mappers/shared";
import type {
  AttractionDetail,
  BottleneckData,
  CaptureDetail,
  OfferSaleData,
  NurtureDetail,
  OpportunityDetail,
  RevenueGroupData,
  SalesDetail,
  AdoptionDetail,
  ExpansionDetailData,
  EvangelizationDetail,
  ExpansionOfferData,
  ExpansionGroupData,
  StageTimeSeries,
  MetricCatalog,
} from "../types/metrics";

// ---------------------------------------------------------------------------
// Raw API response types (snake_case fields, as they arrive from the backend)
// ---------------------------------------------------------------------------
// RawGroup and RawChannel are re-used from mappers/shared.ts (imported above)

interface RawAvailable {
  channels: RawChannel[];
}

interface RawMiniFunnel {
  source_label?: string;
  source_value?: number;
  target_label?: string;
  target_value?: number;
  conversion_rate?: number;
}

interface RawHeaderKpisCapture {
  total_leads: number;
  conversion_rate: number;
  cost_per_lead?: number | null;
}

interface RawHeaderKpisNurture {
  total_mqls: number;
  conversion_rate: number;
  cost_per_mql?: number | null;
}

interface RawHeaderKpisOpportunity {
  total_sqls?: number;
  conversion_rate?: number;
  cost_per_sql?: number | null;
}

interface RawBottleneck {
  type: string;
  metric_label: string;
  current_rate: number;
  severity: "normal" | "warning" | "critical";
  threshold: number;
  tip: string;
}

interface RawAttractionResponse {
  period: string;
  last_updated?: string;
  organic_social: RawGroup;
  ga4_search: RawGroup;
  paid: RawGroup;
  outbound: RawGroup;
  website?: RawGroup;
  available?: RawAvailable;
}

interface RawCaptureResponse {
  header_kpis: RawHeaderKpisCapture;
  mini_funnel: RawMiniFunnel;
  web_infrastructure: RawGroup;
  ai_agent: RawGroup;
  available?: RawAvailable;
  period: string;
  last_updated?: string;
}

interface RawNurtureResponse {
  header_kpis: RawHeaderKpisNurture;
  mini_funnel: RawMiniFunnel;
  retargeting: RawGroup;
  automation: RawGroup;
  available?: RawAvailable;
  period: string;
  last_updated?: string;
}

interface RawOpportunityResponse {
  header_kpis?: RawHeaderKpisOpportunity;
  mini_funnel?: RawMiniFunnel;
  checkout: RawGroup;
  payment_links: RawGroup;
  qualification: RawGroup;
  bottlenecks?: RawBottleneck[];
  available?: RawAvailable;
  period?: string;
  last_updated?: string;
}

interface RawOfferSale {
  offer_id: string;
  public_name: string;
  offer_type: string;
  pricing_type: string;
  total_revenue: number;
  sales_count: number;
  currency: string;
  usd_revenue?: number | null;
  source_breakdown?: Record<string, number>;
  new_subscriptions?: number | null;
  new_subscription_revenue?: number | null;
  renewals?: number | null;
  renewal_revenue?: number | null;
  subscription_new_label?: string | null;
  subscription_renewal_label?: string | null;
}

interface RawTierGroup {
  tier_key: string;
  tier_label: string;
  offers?: RawOfferSale[];
}

interface RawRevenueGroup {
  group_key: string;
  group_label: string;
  total_revenue: number;
  total_revenue_usd?: number | null;
  customer_count: number;
  revenue_percentage: number;
  currency: string;
  tiers?: RawTierGroup[];
}

interface RawSalesHeaderKpis {
  total_revenue?: number;
  total_revenue_usd?: number | null;
  currency?: string;
  new_customers?: number;
  cac?: number | null;
  cac_incomplete?: boolean;
  net_sales?: number;
  total_discounts?: number;
  total_tax?: number;
  refund_count?: number;
  refund_amount?: number;
  shipping_revenue?: number;
  repeat_customers?: number;
  discount_usage_count?: number;
  shopify_revenue?: number;
  shopify_order_count?: number;
  shopify_avg_order_value?: number;
  shopify_currency?: string;
}

interface RawSalesResponse {
  header_kpis?: RawSalesHeaderKpis;
  mini_funnel?: RawMiniFunnel;
  adquisicion: RawRevenueGroup;
  expansion: RawRevenueGroup;
  bottlenecks?: RawBottleneck[];
  period?: string;
  last_updated?: string;
}

interface RawOfferHealth {
  offer_id: string;
  public_name: string;
  total_customers: number;
  active_count: number;
  inactive_count: number;
  health_pct: number;
  ttv_days?: number | null;
}

interface RawAdoptionHeaderKpis {
  active_customers?: number;
  inactive_customers?: number;
  health_pct?: number;
  avg_ttv_days?: number | null;
  refund_count?: number;
  refund_amount?: number;
  refund_currency?: string;
  refund_amount_usd?: number | null;
}

interface RawAdoptionResponse {
  header_kpis?: RawAdoptionHeaderKpis;
  mini_funnel?: RawMiniFunnel;
  offers?: RawOfferHealth[];
  bottlenecks?: RawBottleneck[];
  period?: string;
  last_updated?: string;
}

interface RawExpansionOffer {
  offer_id: string;
  public_name: string;
  count: number;
  revenue: number;
  currency: string;
  usd_revenue?: number | null;
}

interface RawExpansionGroup {
  group_key: string;
  group_label: string;
  group_subtitle: string;
  total_count: number;
  total_revenue: number;
  total_revenue_usd?: number | null;
  currency: string;
  rate_pct?: number | null;
  offers?: RawExpansionOffer[];
}

interface RawExpansionHeaderKpis {
  net_mrr?: number;
  net_mrr_usd?: number | null;
  currency?: string;
  avg_ltv?: number;
  avg_ltv_usd?: number | null;
  churn_rate_pct?: number;
}

interface RawExpansionResponse {
  header_kpis?: RawExpansionHeaderKpis;
  mini_funnel?: RawMiniFunnel;
  retencion: RawExpansionGroup;
  crecimiento: RawExpansionGroup;
  cancelaciones: RawExpansionGroup;
  bottlenecks?: RawBottleneck[];
  period?: string;
  last_updated?: string;
}

interface RawEvangelist {
  customer_id: string;
  full_name: string;
  referral_code: string;
  referrals_sent: number;
  conversions: number;
  revenue_attributed: number;
  currency?: string;
  usd_revenue?: number | null;
  is_active: boolean;
}

interface RawCandidato {
  customer_id: string;
  full_name: string;
  nps_score: number;
  responded_at?: string | null;
}

interface RawNpsSummary {
  nps_score?: number | null;
  standard_nps?: number | null;
  promoter_count?: number;
  passive_count?: number;
  detractor_count?: number;
  total_responses?: number;
  surveys_sent?: number;
  response_rate_pct?: number;
}

interface RawEvangelizationHeaderKpis {
  k_factor?: number;
  referral_conversions?: number;
  nps_score?: number | null;
  referral_revenue?: number;
  referral_revenue_usd?: number | null;
  currency?: string;
  active_evangelists?: number;
}

interface RawEvangelizationResponse {
  header_kpis?: RawEvangelizationHeaderKpis;
  mini_funnel?: RawMiniFunnel;
  referidos?: RawEvangelist[];
  candidatos?: RawCandidato[];
  nps_summary?: RawNpsSummary;
  ugc_count?: number;
  ugc_written?: number;
  ugc_audio?: number;
  bottlenecks?: RawBottleneck[];
  period?: string;
  last_updated?: string;
}

// ---------------------------------------------------------------------------

const API_URL = config.api.baseUrl;

function mapBottleneck(b: RawBottleneck): BottleneckData {
  return {
    type: b.type as BottleneckData["type"],
    metricLabel: b.metric_label,
    currentRate: b.current_rate,
    severity: b.severity,
    threshold: b.threshold,
    tip: b.tip,
  };
}

function mapResponse(raw: RawAttractionResponse): AttractionDetail {
  return {
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
    organicSocial: mapGroup(raw.organic_social),
    ga4Search: mapGroup(raw.ga4_search),
    paid: mapGroup(raw.paid),
    outbound: mapGroup(raw.outbound),
    website: raw.website ? mapGroup(raw.website) : undefined,
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
  };
}

function mapCaptureResponse(raw: RawCaptureResponse): CaptureDetail {
  return {
    headerKpis: {
      totalLeads: raw.header_kpis.total_leads,
      conversionRate: raw.header_kpis.conversion_rate,
      costPerLead: raw.header_kpis.cost_per_lead ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel.source_label ?? "",
      sourceValue: raw.mini_funnel.source_value ?? 0,
      targetLabel: raw.mini_funnel.target_label ?? "",
      targetValue: raw.mini_funnel.target_value ?? 0,
      conversionRate: raw.mini_funnel.conversion_rate ?? 0,
    },
    webInfrastructure: mapGroup(raw.web_infrastructure),
    aiAgent: mapGroup(raw.ai_agent),
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
  };
}

function mapNurtureResponse(raw: RawNurtureResponse): NurtureDetail {
  return {
    headerKpis: {
      totalMqls: raw.header_kpis.total_mqls,
      conversionRate: raw.header_kpis.conversion_rate,
      costPerMql: raw.header_kpis.cost_per_mql ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel.source_label ?? "",
      sourceValue: raw.mini_funnel.source_value ?? 0,
      targetLabel: raw.mini_funnel.target_label ?? "",
      targetValue: raw.mini_funnel.target_value ?? 0,
      conversionRate: raw.mini_funnel.conversion_rate ?? 0,
    },
    retargeting: mapGroup(raw.retargeting),
    automation: mapGroup(raw.automation),
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
  };
}

function mapOpportunityResponse(raw: RawOpportunityResponse): OpportunityDetail {
  return {
    headerKpis: {
      totalSqls: raw.header_kpis?.total_sqls ?? 0,
      conversionRate: raw.header_kpis?.conversion_rate ?? 0,
      costPerSql: raw.header_kpis?.cost_per_sql ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? "MQLs",
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? "SQLs",
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    checkout: mapGroup(raw.checkout),
    paymentLinks: mapGroup(raw.payment_links),
    qualification: mapGroup(raw.qualification),
    bottlenecks: (raw.bottlenecks ?? []).map(mapBottleneck),
    available: raw.available
      ? { channels: (raw.available.channels ?? []).map(mapChannel) }
      : undefined,
    period: raw.period ?? "last_30_days",
    lastUpdated: raw.last_updated,
  };
}

function mapOfferSale(o: RawOfferSale): OfferSaleData {
  return {
    offerId: o.offer_id,
    publicName: o.public_name,
    offerType: o.offer_type,
    pricingType: o.pricing_type as OfferSaleData["pricingType"],
    totalRevenue: o.total_revenue,
    salesCount: o.sales_count,
    currency: o.currency,
    usdRevenue: o.usd_revenue ?? null,
    sourceBreakdown: o.source_breakdown ?? {},
    newSubscriptions: o.new_subscriptions ?? null,
    newSubscriptionRevenue: o.new_subscription_revenue ?? null,
    renewals: o.renewals ?? null,
    renewalRevenue: o.renewal_revenue ?? null,
    subscriptionNewLabel: o.subscription_new_label ?? null,
    subscriptionRenewalLabel: o.subscription_renewal_label ?? null,
  };
}

function mapTier(t: RawTierGroup) {
  return {
    tierKey: t.tier_key,
    tierLabel: t.tier_label,
    offers: (t.offers ?? []).map(mapOfferSale),
  };
}

function mapRevenueGroup(g: RawRevenueGroup): RevenueGroupData {
  return {
    groupKey: g.group_key as RevenueGroupData["groupKey"],
    groupLabel: g.group_label,
    totalRevenue: g.total_revenue,
    totalRevenueUsd: g.total_revenue_usd ?? null,
    customerCount: g.customer_count,
    revenuePercentage: g.revenue_percentage,
    currency: g.currency,
    tiers: (g.tiers ?? []).map(mapTier),
  };
}

function mapSalesResponse(raw: RawSalesResponse): SalesDetail {
  return {
    headerKpis: {
      totalRevenue: raw.header_kpis?.total_revenue ?? 0,
      totalRevenueUsd: raw.header_kpis?.total_revenue_usd ?? null,
      currency: raw.header_kpis?.currency ?? "MXN",
      newCustomers: raw.header_kpis?.new_customers ?? 0,
      cac: raw.header_kpis?.cac ?? null,
      cacIncomplete: raw.header_kpis?.cac_incomplete ?? false,
      netSales: raw.header_kpis?.net_sales ?? 0,
      totalDiscounts: raw.header_kpis?.total_discounts ?? 0,
      totalTax: raw.header_kpis?.total_tax ?? 0,
      refundCount: raw.header_kpis?.refund_count ?? 0,
      refundAmount: raw.header_kpis?.refund_amount ?? 0,
      shippingRevenue: raw.header_kpis?.shipping_revenue ?? 0,
      repeatCustomers: raw.header_kpis?.repeat_customers ?? 0,
      discountUsageCount: raw.header_kpis?.discount_usage_count ?? 0,
      shopifyRevenue: raw.header_kpis?.shopify_revenue ?? 0,
      shopifyOrderCount: raw.header_kpis?.shopify_order_count ?? 0,
      shopifyAvgOrderValue: raw.header_kpis?.shopify_avg_order_value ?? 0,
      shopifyCurrency: raw.header_kpis?.shopify_currency ?? "USD",
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? "Oportunidades",
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? "Ventas",
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    adquisicion: mapRevenueGroup(raw.adquisicion),
    expansion: mapRevenueGroup(raw.expansion),
    bottlenecks: (raw.bottlenecks ?? []).map(mapBottleneck),
    period: raw.period ?? "last_30_days",
    lastUpdated: raw.last_updated,
  };
}

function mapAdoptionResponse(raw: RawAdoptionResponse): AdoptionDetail {
  return {
    headerKpis: {
      activeCustomers: raw.header_kpis?.active_customers ?? 0,
      inactiveCustomers: raw.header_kpis?.inactive_customers ?? 0,
      healthPct: raw.header_kpis?.health_pct ?? 0,
      avgTtvDays: raw.header_kpis?.avg_ttv_days ?? null,
      refundCount: raw.header_kpis?.refund_count ?? 0,
      refundAmount: raw.header_kpis?.refund_amount ?? 0,
      refundCurrency: raw.header_kpis?.refund_currency ?? "USD",
      refundAmountUsd: raw.header_kpis?.refund_amount_usd ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? "Ventas",
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? "Activos",
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    offers: (raw.offers ?? []).map((o: RawOfferHealth) => ({
      offerId: o.offer_id,
      publicName: o.public_name,
      totalCustomers: o.total_customers,
      activeCount: o.active_count,
      inactiveCount: o.inactive_count,
      healthPct: o.health_pct,
      ttvDays: o.ttv_days ?? null,
    })),
    bottlenecks: (raw.bottlenecks ?? []).map(mapBottleneck),
    period: raw.period ?? "last_30_days",
    lastUpdated: raw.last_updated,
  };
}

function mapExpansionOffer(o: RawExpansionOffer): ExpansionOfferData {
  return {
    offerId: o.offer_id,
    publicName: o.public_name,
    count: o.count,
    revenue: o.revenue,
    currency: o.currency,
    usdRevenue: o.usd_revenue ?? null,
  };
}

function mapExpansionGroup(g: RawExpansionGroup): ExpansionGroupData {
  return {
    groupKey: g.group_key as ExpansionGroupData["groupKey"],
    groupLabel: g.group_label,
    groupSubtitle: g.group_subtitle,
    totalCount: g.total_count,
    totalRevenue: g.total_revenue,
    totalRevenueUsd: g.total_revenue_usd ?? null,
    currency: g.currency,
    ratePct: g.rate_pct ?? null,
    offers: (g.offers ?? []).map(mapExpansionOffer),
  };
}

function mapExpansionResponse(raw: RawExpansionResponse): ExpansionDetailData {
  return {
    headerKpis: {
      netMrr: raw.header_kpis?.net_mrr ?? 0,
      netMrrUsd: raw.header_kpis?.net_mrr_usd ?? null,
      currency: raw.header_kpis?.currency ?? "MXN",
      avgLtv: raw.header_kpis?.avg_ltv ?? 0,
      avgLtvUsd: raw.header_kpis?.avg_ltv_usd ?? null,
      churnRatePct: raw.header_kpis?.churn_rate_pct ?? 0,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? "Activos",
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? "Expansion",
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    retencion: mapExpansionGroup(raw.retencion),
    crecimiento: mapExpansionGroup(raw.crecimiento),
    cancelaciones: mapExpansionGroup(raw.cancelaciones),
    bottlenecks: (raw.bottlenecks ?? []).map(mapBottleneck),
    period: raw.period ?? "last_30_days",
    lastUpdated: raw.last_updated,
  };
}

function mapEvangelizationResponse(raw: RawEvangelizationResponse): EvangelizationDetail {
  return {
    headerKpis: {
      kFactor: raw.header_kpis?.k_factor ?? 0,
      referralConversions: raw.header_kpis?.referral_conversions ?? 0,
      npsScore: raw.header_kpis?.nps_score ?? null,
      referralRevenue: raw.header_kpis?.referral_revenue ?? 0,
      referralRevenueUsd: raw.header_kpis?.referral_revenue_usd ?? null,
      currency: raw.header_kpis?.currency ?? "MXN",
      activeEvangelists: raw.header_kpis?.active_evangelists ?? 0,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? "Clientes Activos",
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? "Evangelistas",
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    referidos: (raw.referidos ?? []).map((e: RawEvangelist) => ({
      customerId: e.customer_id,
      fullName: e.full_name,
      referralCode: e.referral_code,
      referralsSent: e.referrals_sent,
      conversions: e.conversions,
      revenueAttributed: e.revenue_attributed,
      currency: e.currency ?? "MXN",
      usdRevenue: e.usd_revenue ?? null,
      isActive: e.is_active,
    })),
    candidatos: (raw.candidatos ?? []).map((c: RawCandidato) => ({
      customerId: c.customer_id,
      fullName: c.full_name,
      npsScore: c.nps_score,
      respondedAt: c.responded_at ?? null,
    })),
    npsSummary: {
      npsScore: raw.nps_summary?.nps_score ?? null,
      standardNps: raw.nps_summary?.standard_nps ?? null,
      promoterCount: raw.nps_summary?.promoter_count ?? 0,
      passiveCount: raw.nps_summary?.passive_count ?? 0,
      detractorCount: raw.nps_summary?.detractor_count ?? 0,
      totalResponses: raw.nps_summary?.total_responses ?? 0,
      surveysSent: raw.nps_summary?.surveys_sent ?? 0,
      responseRatePct: raw.nps_summary?.response_rate_pct ?? 0,
    },
    ugcCount: raw.ugc_count ?? 0,
    ugcWritten: raw.ugc_written ?? 0,
    ugcAudio: raw.ugc_audio ?? 0,
    bottlenecks: (raw.bottlenecks ?? []).map(mapBottleneck),
    period: raw.period ?? "last_30_days",
    lastUpdated: raw.last_updated,
  };
}

export type PeriodType = "last_30_days" | "weekly" | "monthly" | "quarterly";

function buildPeriodUrl(base: string, period?: PeriodType): string {
  if (!period || period === "last_30_days") return base;
  const sep = base.includes("?") ? "&" : "?";
  return `${base}${sep}period=${period}`;
}

export const metricsApi = {
  getAttractionDetail: async (token: string, period?: PeriodType): Promise<AttractionDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_ATTRACTION_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_ATTRACTION_DETAIL;
    }
    const res = await fetchClient(
      buildPeriodUrl(`${API_URL}/api/v1/analytics/metrics/attraction`, period),
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error(`Attraction API returned ${res.status}`);
    const data = (await res.json()) as RawAttractionResponse;
    return mapResponse(data);
  },

  getCaptureDetail: async (token: string, period?: PeriodType): Promise<CaptureDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_CAPTURE_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_CAPTURE_DETAIL;
    }
    const res = await fetchClient(
      buildPeriodUrl(`${API_URL}/api/v1/analytics/metrics/capture`, period),
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error(`Capture API returned ${res.status}`);
    const data = (await res.json()) as RawCaptureResponse;
    return mapCaptureResponse(data);
  },

  getNurtureDetail: async (token: string, period?: PeriodType): Promise<NurtureDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_NURTURE_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_NURTURE_DETAIL;
    }
    const res = await fetchClient(
      buildPeriodUrl(`${API_URL}/api/v1/analytics/metrics/nurturing`, period),
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error(`Nurture API returned ${res.status}`);
    const data = (await res.json()) as RawNurtureResponse;
    return mapNurtureResponse(data);
  },

  getOpportunityDetail: async (token: string): Promise<OpportunityDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_OPPORTUNITY_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_OPPORTUNITY_DETAIL;
    }
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/opportunity`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Opportunity API returned ${res.status}`);
    const data = (await res.json()) as RawOpportunityResponse;
    return mapOpportunityResponse(data);
  },

  getSalesDetail: async (token: string): Promise<SalesDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_SALES_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_SALES_DETAIL;
    }
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/sales`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Sales API returned ${res.status}`);
    const data = (await res.json()) as RawSalesResponse;
    return mapSalesResponse(data);
  },

  getAdoptionDetail: async (token: string): Promise<AdoptionDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_ADOPTION_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_ADOPTION_DETAIL;
    }
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/adoption`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Adoption API returned ${res.status}`);
    const data = (await res.json()) as RawAdoptionResponse;
    return mapAdoptionResponse(data);
  },

  getExpansionDetail: async (token: string): Promise<ExpansionDetailData> => {
    if (ENABLE_MOCKS) {
      const { MOCK_EXPANSION_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_EXPANSION_DETAIL;
    }
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/expansion`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Expansion API returned ${res.status}`);
    const data = (await res.json()) as RawExpansionResponse;
    return mapExpansionResponse(data);
  },

  getEvangelizationDetail: async (token: string): Promise<EvangelizationDetail> => {
    if (ENABLE_MOCKS) {
      const { MOCK_EVANGELIZATION_DETAIL } = await import("../__mocks__/metrics-mock-data");
      return MOCK_EVANGELIZATION_DETAIL;
    }
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/evangelization`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Evangelization API returned ${res.status}`);
    const data = (await res.json()) as RawEvangelizationResponse;
    return mapEvangelizationResponse(data);
  },

  getMetricCatalog: async (token: string): Promise<MetricCatalog> => {
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/catalog`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Metric catalog API returned ${res.status}`);
    return res.json() as Promise<MetricCatalog>;
  },

  // eslint-disable-next-line max-params -- public API; grouping into options object would require updating all callers
  getTimeSeries: async (
    token: string,
    stage: string,
    metric: string,
    rangeDays: number,
    granularity: string,
  ): Promise<StageTimeSeries> => {
    if (ENABLE_MOCKS) {
      const { MOCK_TIME_SERIES } = await import("../__mocks__/metrics-mock-data");
      return MOCK_TIME_SERIES;
    }
    const params = new URLSearchParams({
      stage,
      metric,
      range_days: String(rangeDays),
      granularity,
    });
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/timeseries?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`TimeSeries API returned ${res.status}`);
    const raw = (await res.json()) as {
      stage: string;
      metric_name: string;
      granularity: "daily" | "weekly";
      range_days: number;
      data_points: { date: string; channels: Record<string, number> }[];
      channels_present: { slug: string; name: string; color: string }[];
      period_totals: Record<string, number>;
      previous_period_totals?: Record<string, number> | null;
    };
    return {
      stage: raw.stage,
      metricName: raw.metric_name,
      granularity: raw.granularity,
      rangeDays: raw.range_days,
      dataPoints: raw.data_points.map((dp) => ({
        date: dp.date,
        channels: dp.channels,
      })),
      channelsPresent: raw.channels_present.map((ch) => ({
        slug: ch.slug,
        name: ch.name,
        color: ch.color,
      })),
      periodTotals: raw.period_totals,
      previousPeriodTotals: raw.previous_period_totals ?? null,
    };
  },
};
