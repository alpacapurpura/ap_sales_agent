import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import { ENABLE_MOCKS } from '@/lib/mock-config';
import type { AttractionDetail, CaptureDetail, NurtureDetail, OpportunityDetail, SalesDetail, ChannelMetric, MetricValue } from '../types/metrics';
import { MOCK_ATTRACTION_DETAIL, MOCK_CAPTURE_DETAIL, MOCK_NURTURE_DETAIL, MOCK_OPPORTUNITY_DETAIL, MOCK_SALES_DETAIL } from './metrics-mock-data';

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
      sourceValue: raw.mini_funnel?.source_count ?? 0,
      targetLabel: raw.mini_funnel?.target_label ?? 'Ventas',
      targetValue: raw.mini_funnel?.target_count ?? 0,
      conversionRate: raw.mini_funnel?.conversion_rate ?? 0,
    },
    adquisicion: mapRevenueGroup(raw.adquisicion),
    expansion: mapRevenueGroup(raw.expansion),
    bottlenecks: (raw.bottlenecks ?? []).map((b: any) => ({
      type: b.type,
      severity: b.severity,
      message: b.message,
      tip: b.tip,
    })),
    period: raw.period ?? 'last_30_days',
    lastUpdated: raw.last_updated,
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

  getCaptureDetail: async (token: string): Promise<CaptureDetail> => {
    if (ENABLE_MOCKS) {
      return MOCK_CAPTURE_DETAIL;
    }

    try {
      const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/capture`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.warn('Capture API returned', res.status, '-- using mock data');
        return MOCK_CAPTURE_DETAIL;
      }

      const data = await res.json();
      return mapCaptureResponse(data);
    } catch (error) {
      console.warn('Capture API error -- using mock data:', error);
      return MOCK_CAPTURE_DETAIL;
    }
  },

  getNurtureDetail: async (token: string): Promise<NurtureDetail> => {
    if (ENABLE_MOCKS) {
      return MOCK_NURTURE_DETAIL;
    }

    try {
      const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/nurturing`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.warn('Nurture API returned', res.status, '-- using mock data');
        return MOCK_NURTURE_DETAIL;
      }

      const data = await res.json();
      return mapNurtureResponse(data);
    } catch (error) {
      console.warn('Nurture API error -- using mock data:', error);
      return MOCK_NURTURE_DETAIL;
    }
  },

  getOpportunityDetail: async (token: string): Promise<OpportunityDetail> => {
    if (ENABLE_MOCKS) {
      return MOCK_OPPORTUNITY_DETAIL;
    }

    try {
      const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/opportunity`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.warn('Opportunity API returned', res.status, '-- using mock data');
        return MOCK_OPPORTUNITY_DETAIL;
      }

      const data = await res.json();
      return mapOpportunityResponse(data);
    } catch (error) {
      console.warn('Opportunity API error -- using mock data:', error);
      return MOCK_OPPORTUNITY_DETAIL;
    }
  },

  getSalesDetail: async (token: string): Promise<SalesDetail> => {
    if (ENABLE_MOCKS) {
      return MOCK_SALES_DETAIL;
    }

    try {
      const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/sales`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        console.warn('Sales API returned', res.status, '-- using mock data');
        return MOCK_SALES_DETAIL;
      }

      const data = await res.json();
      return mapSalesResponse(data);
    } catch (error) {
      console.warn('Sales API error -- using mock data:', error);
      return MOCK_SALES_DETAIL;
    }
  },
};
