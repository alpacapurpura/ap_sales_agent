import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";
import type { ChannelDashboardData, MetaAdsPeriod } from "../types/metrics";

const API_URL = config.api.baseUrl;

interface ChannelDashboardResponse {
  channel_slug: string;
  channel_name: string;
  industry_category: string;
  period: string;
  kpis: Array<{
    metric_name: string;
    display_name: string;
    current_value: number;
    previous_value: number | null;
    delta_percent: number | null;
    delta_absolute: number | null;
    unit: string;
    currency: string | null;
    higher_is_better: boolean;
    benchmark: {
      low: number;
      median: number;
      high: number;
      unit: string;
      interpretation: string;
    } | null;
  }>;
  time_series: Array<{
    metric_name: string;
    display_name: string;
    unit: string;
    data_points: Array<{ date: string; value: number }>;
  }>;
  funnel: {
    steps: Array<{
      label: string;
      metric_name: string;
      value: number;
      conversion_rate_from_previous: number | null;
    }>;
  };
  frequency_alert: {
    current_value: number;
    severity: string;
    message: string;
  } | null;
  extra_data?: Record<string, unknown> | null;
}

function mapResponse(raw: ChannelDashboardResponse): ChannelDashboardData {
  return {
    channelSlug: raw.channel_slug,
    channelName: raw.channel_name,
    industryCategory: raw.industry_category,
    period: raw.period,
    kpis: raw.kpis.map((k) => ({
      metricName: k.metric_name,
      displayName: k.display_name,
      currentValue: k.current_value,
      previousValue: k.previous_value,
      deltaPct: k.delta_percent,
      deltaAbsolute: k.delta_absolute,
      unit: k.unit,
      currency: k.currency ?? undefined,
      higherIsBetter: k.higher_is_better,
      benchmark: k.benchmark,
    })),
    timeSeries: raw.time_series.map((ts) => ({
      metricName: ts.metric_name,
      displayName: ts.display_name,
      unit: ts.unit,
      dataPoints: ts.data_points,
    })),
    funnel: {
      steps: raw.funnel.steps.map((s) => ({
        label: s.label,
        metricName: s.metric_name,
        value: s.value,
        conversionRate: s.conversion_rate_from_previous,
      })),
    },
    frequencyAlert: raw.frequency_alert
      ? {
          currentValue: raw.frequency_alert.current_value,
          severity: raw.frequency_alert.severity as "warning" | "critical",
          message: raw.frequency_alert.message,
        }
      : null,
    extraData: raw.extra_data ?? null,
  };
}

export async function fetchChannelDashboard(
  token: string,
  channelSlug: string,
  period: MetaAdsPeriod = "30d",
): Promise<ChannelDashboardData> {
  const url = `${API_URL}/api/v1/analytics/metrics/channel/${channelSlug}/dashboard?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Channel Dashboard API returned ${res.status}`);
  const json: ChannelDashboardResponse = await res.json();
  return mapResponse(json);
}
