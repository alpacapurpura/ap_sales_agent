import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { ENABLE_MOCKS } from '@/lib/mock-config';
import type { AttractionDetail, CaptureDetail, NurtureDetail, OpportunityDetail, SalesDetail, AdoptionDetail, ExpansionDetailData, EvangelizationDetail, ChannelMetric, MetricValue, ExpansionOfferData, ExpansionGroupData } from '../types/metrics';
import { MOCK_ATTRACTION_DETAIL, MOCK_CAPTURE_DETAIL, MOCK_NURTURE_DETAIL, MOCK_OPPORTUNITY_DETAIL, MOCK_SALES_DETAIL, MOCK_ADOPTION_DETAIL, MOCK_EXPANSION_DETAIL, MOCK_EVANGELIZATION_DETAIL } from './metrics-mock-data';

const API_URL = config.api.baseUrl;

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
function mapCaptureResponse(raw: any): CaptureDetail {
  return {
    headerKpis: {
      totalLeads: raw.header_kpis.total_leads,
      conversionRate: raw.header_kpis.conversion_rate,
      costPerLead: raw.header_kpis.cost_per_lead ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel.source_label,
      sourceValue: raw.mini_funnel.source_value,
      targetLabel: raw.mini_funnel.target_label,
      targetValue: raw.mini_funnel.target_value,
      conversionRate: raw.mini_funnel.conversion_rate,
    },
    webInfrastructure: mapGroup(raw.web_infrastructure),
    aiAgent: mapGroup(raw.ai_agent),
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
  };
}
function mapNurtureResponse(raw: any): NurtureDetail {
  return {
    headerKpis: {
      totalMqls: raw.header_kpis.total_mqls,
      conversionRate: raw.header_kpis.conversion_rate,
      costPerMql: raw.header_kpis.cost_per_mql ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel.source_label,
      sourceValue: raw.mini_funnel.source_value,
      targetLabel: raw.mini_funnel.target_label,
      targetValue: raw.mini_funnel.target_value,
      conversionRate: raw.mini_funnel.conversion_rate,
    },
    retargeting: mapGroup(raw.retargeting),
    automation: mapGroup(raw.automation),
    available: raw.available ? { channels: raw.available.channels.map(mapChannel) } : undefined,
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
  };
}
function mapOpportunityResponse(raw: any): OpportunityDetail {
  return {
    headerKpis: {
      totalSqls: raw.header_kpis?.total_sqls ?? 0,
      conversionRate: raw.header_kpis?.conversion_rate ?? 0,
      costPerSql: raw.header_kpis?.cost_per_sql ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? 'MQLs',
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'SQLs',
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    checkout: mapGroup(raw.checkout),
    paymentLinks: mapGroup(raw.payment_links),
    qualification: mapGroup(raw.qualification),
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      metricLabel: b.metric_label,
      currentRate: b.current_rate,
      severity: b.severity,
      threshold: b.threshold,
      tip: b.tip,
    })),
    available: raw.available ? { channels: (raw.available.channels ?? []).map(mapChannel) } : undefined,
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
  };
}
function mapSalesResponse(raw: any): SalesDetail {
  const mapOffer = (o: any) => ({
    offerId: o.offer_id,
    publicName: o.public_name,
    offerType: o.offer_type,
    pricingType: o.pricing_type,
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
  });

  const mapTier = (t: any) => ({
    tierKey: t.tier_key,
    tierLabel: t.tier_label,
    offers: (t.offers ?? []).map(mapOffer),
  });

  const mapRevenueGroup = (g: any) => ({
    groupKey: g.group_key,
    groupLabel: g.group_label,
    totalRevenue: g.total_revenue,
    totalRevenueUsd: g.total_revenue_usd ?? null,
    customerCount: g.customer_count,
    revenuePercentage: g.revenue_percentage,
    currency: g.currency,
    tiers: (g.tiers ?? []).map(mapTier),
  });

  return {
    headerKpis: {
      totalRevenue: raw.header_kpis?.total_revenue ?? 0,
      totalRevenueUsd: raw.header_kpis?.total_revenue_usd ?? null,
      currency: raw.header_kpis?.currency ?? 'MXN',
      newCustomers: raw.header_kpis?.new_customers ?? 0,
      cac: raw.header_kpis?.cac ?? null,
      cacIncomplete: raw.header_kpis?.cac_incomplete ?? false,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? 'Oportunidades',
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'Ventas',
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    adquisicion: mapRevenueGroup(raw.adquisicion),
    expansion: mapRevenueGroup(raw.expansion),
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      metricLabel: b.metric_label,
      currentRate: b.current_rate,
      severity: b.severity,
      threshold: b.threshold,
      tip: b.tip,
    })),
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
  };
}
function mapAdoptionResponse(raw: any): AdoptionDetail {
  return {
    headerKpis: {
      activeCustomers: raw.header_kpis?.active_customers ?? 0,
      inactiveCustomers: raw.header_kpis?.inactive_customers ?? 0,
      healthPct: raw.header_kpis?.health_pct ?? 0,
      avgTtvDays: raw.header_kpis?.avg_ttv_days ?? null,
      refundCount: raw.header_kpis?.refund_count ?? 0,
      refundAmount: raw.header_kpis?.refund_amount ?? 0,
      refundCurrency: raw.header_kpis?.refund_currency ?? 'USD',
      refundAmountUsd: raw.header_kpis?.refund_amount_usd ?? null,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? 'Ventas',
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'Activos',
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    offers: (raw.offers ?? []).map((o: any) => ({
      offerId: o.offer_id,
      publicName: o.public_name,
      totalCustomers: o.total_customers,
      activeCount: o.active_count,
      inactiveCount: o.inactive_count,
      healthPct: o.health_pct,
      ttvDays: o.ttv_days ?? null,
    })),
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      metricLabel: b.metric_label,
      currentRate: b.current_rate,
      severity: b.severity,
      threshold: b.threshold,
      tip: b.tip,
    })),
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
  };
}
function mapExpansionOffer(o: any): ExpansionOfferData {
  return {
    offerId: o.offer_id,
    publicName: o.public_name,
    count: o.count,
    revenue: o.revenue,
    currency: o.currency,
    usdRevenue: o.usd_revenue ?? null,
  };
}

function mapExpansionGroup(g: any): ExpansionGroupData {
  return {
    groupKey: g.group_key,
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

function mapExpansionResponse(raw: any): ExpansionDetailData {
  return {
    headerKpis: {
      netMrr: raw.header_kpis?.net_mrr ?? 0,
      netMrrUsd: raw.header_kpis?.net_mrr_usd ?? null,
      currency: raw.header_kpis?.currency ?? 'MXN',
      avgLtv: raw.header_kpis?.avg_ltv ?? 0,
      avgLtvUsd: raw.header_kpis?.avg_ltv_usd ?? null,
      churnRatePct: raw.header_kpis?.churn_rate_pct ?? 0,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? 'Activos',
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'Expansion',
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    retencion: mapExpansionGroup(raw.retencion),
    crecimiento: mapExpansionGroup(raw.crecimiento),
    cancelaciones: mapExpansionGroup(raw.cancelaciones),
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      metricLabel: b.metric_label,
      currentRate: b.current_rate,
      severity: b.severity,
      threshold: b.threshold,
      tip: b.tip,
    })),
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
  };
}
function mapEvangelizationResponse(raw: any): EvangelizationDetail {
  return {
    headerKpis: {
      kFactor: raw.header_kpis?.k_factor ?? 0,
      referralConversions: raw.header_kpis?.referral_conversions ?? 0,
      npsScore: raw.header_kpis?.nps_score ?? null,
      referralRevenue: raw.header_kpis?.referral_revenue ?? 0,
      referralRevenueUsd: raw.header_kpis?.referral_revenue_usd ?? null,
      currency: raw.header_kpis?.currency ?? 'MXN',
      activeEvangelists: raw.header_kpis?.active_evangelists ?? 0,
    },
    miniFunnel: {
      sourceLabel: raw.mini_funnel?.source_label ?? 'Clientes Activos',
      sourceValue: raw.mini_funnel?.source_value ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'Evangelistas',
      targetValue: raw.mini_funnel?.target_value ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    referidos: (raw.referidos ?? []).map((e: any) => ({
      customerId: e.customer_id,
      fullName: e.full_name,
      referralCode: e.referral_code,
      referralsSent: e.referrals_sent,
      conversions: e.conversions,
      revenueAttributed: e.revenue_attributed,
      currency: e.currency ?? 'MXN',
      usdRevenue: e.usd_revenue ?? null,
      isActive: e.is_active,
    })),
    candidatos: (raw.candidatos ?? []).map((c: any) => ({
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
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      metricLabel: b.metric_label,
      currentRate: b.current_rate,
      severity: b.severity,
      threshold: b.threshold,
      tip: b.tip,
    })),
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
  };
}

// --- Product Mapping Types ---
export interface UnmatchedProduct {
  external_id: string;
  external_name: string | null;
  total_price: number | null;
  currency: string | null;
  event_count: number;
}

export interface ProductMapping {
  id: string;
  tenant_id: string;
  offer_id: string;
  source: string;
  external_id: string;
  external_name: string | null;
  metadata_info: Record<string, unknown>;
}

export const metricsApi = {
  getAttractionDetail: async (token: string): Promise<AttractionDetail> => {
    if (ENABLE_MOCKS) return MOCK_ATTRACTION_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/attraction`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Attraction API returned ${res.status}`);
    const data = await res.json();
    return mapResponse(data);
  },

  getCaptureDetail: async (token: string): Promise<CaptureDetail> => {
    if (ENABLE_MOCKS) return MOCK_CAPTURE_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/capture`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Capture API returned ${res.status}`);
    const data = await res.json();
    return mapCaptureResponse(data);
  },

  getNurtureDetail: async (token: string): Promise<NurtureDetail> => {
    if (ENABLE_MOCKS) return MOCK_NURTURE_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/nurturing`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Nurture API returned ${res.status}`);
    const data = await res.json();
    return mapNurtureResponse(data);
  },

  getOpportunityDetail: async (token: string): Promise<OpportunityDetail> => {
    if (ENABLE_MOCKS) return MOCK_OPPORTUNITY_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/opportunity`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Opportunity API returned ${res.status}`);
    const data = await res.json();
    return mapOpportunityResponse(data);
  },

  getSalesDetail: async (token: string): Promise<SalesDetail> => {
    if (ENABLE_MOCKS) return MOCK_SALES_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/sales`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Sales API returned ${res.status}`);
    const data = await res.json();
    return mapSalesResponse(data);
  },

  getAdoptionDetail: async (token: string): Promise<AdoptionDetail> => {
    if (ENABLE_MOCKS) return MOCK_ADOPTION_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/adoption`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Adoption API returned ${res.status}`);
    const data = await res.json();
    return mapAdoptionResponse(data);
  },

  getExpansionDetail: async (token: string): Promise<ExpansionDetailData> => {
    if (ENABLE_MOCKS) return MOCK_EXPANSION_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/expansion`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Expansion API returned ${res.status}`);
    const data = await res.json();
    return mapExpansionResponse(data);
  },

  getEvangelizationDetail: async (token: string): Promise<EvangelizationDetail> => {
    if (ENABLE_MOCKS) return MOCK_EVANGELIZATION_DETAIL;
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/evangelization`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Evangelization API returned ${res.status}`);
    const data = await res.json();
    return mapEvangelizationResponse(data);
  },

  promoteToEvangelist: async (token: string, customerId: string): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/crm/referrals/promote`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId }),
    });
    if (!res.ok) throw new Error('Failed to promote');
    return res.json();
  },

  createNpsSurvey: async (token: string, payload: { customer_id?: string; offer_id?: string; delivery_channel?: string }): Promise<any> => {
    const res = await fetchClient(`${API_URL}/api/v1/crm/nps/surveys`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create survey');
    return res.json();
  },

  getUnmatchedProducts: async (token: string, source: string = 'shopify'): Promise<UnmatchedProduct[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings/unmatched?source=${source}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    return res.json();
  },

  getProductMappings: async (token: string, source: string = 'shopify'): Promise<ProductMapping[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings?source=${source}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return [];
    return res.json();
  },

  createProductMapping: async (token: string, payload: { offer_id: string; source: string; external_id: string; external_name?: string }): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create mapping');
    }
  },

  deleteProductMapping: async (token: string, mappingId: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/offer/product-mappings/${mappingId}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error('Failed to delete mapping');
  },

  triggerInitialLoad: async (token: string, provider: string, days: number = 30): Promise<{
    status: string;
    total_days: number;
    loaded_days: number;
    skipped_days: number;
  }> => {
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/${provider}/initial-load?days=${days}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Initial load failed (${res.status})`);
    }
    return res.json();
  },

  getInitialLoadStatus: async (token: string, provider: string): Promise<{
    status: string;
    total_days?: number;
    completed_days?: number;
  }> => {
    const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/${provider}/initial-load/status`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return { status: 'idle' };
    return res.json();
  },
};
