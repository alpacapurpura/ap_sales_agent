import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  StageOverview,
  ChannelOverview,
  GroupOverview,
  OverviewMiniFunnel,
  OverviewBottleneck,
  ChannelMetric,
} from "../types/metrics";

const API_URL = config.api.baseUrl;

function mapChannelOverview(raw: Record<string, unknown>): ChannelOverview {
  return {
    slug: raw.slug as string,
    name: raw.name as string,
    channelType: raw.channel_type as string,
    groupKey: raw.group_key as string,
    connected: raw.connected as boolean,
    headlineKpi: raw.headline_kpi
      ? {
          name: (raw.headline_kpi as Record<string, unknown>).name as string,
          value: (raw.headline_kpi as Record<string, unknown>).value as number,
          unit: (raw.headline_kpi as Record<string, unknown>).unit as string | undefined,
        }
      : null,
    lastUpdated: raw.last_updated as string | undefined,
    stale: (raw.stale as boolean) ?? false,
    providerName: raw.provider_name as string | undefined,
  };
}

function mapGroupOverview(raw: Record<string, unknown>): GroupOverview {
  return {
    groupKey: raw.group_key as string,
    groupLabel: raw.group_label as string,
    channelCount: raw.channel_count as number,
  };
}

function mapMiniFunnel(raw: Record<string, unknown> | null): OverviewMiniFunnel | null {
  if (!raw) return null;
  return {
    sourceLabel: raw.source_label as string,
    sourceValue: raw.source_value as number,
    targetLabel: raw.target_label as string,
    targetValue: raw.target_value as number,
    conversionRate: raw.conversion_rate as number,
  };
}

function mapBottleneck(raw: Record<string, unknown>): OverviewBottleneck {
  return {
    type: raw.type as string,
    metricLabel: raw.metric_label as string,
    severity: raw.severity as string,
  };
}

function mapStageOverview(raw: Record<string, unknown>): StageOverview {
  return {
    stage: raw.stage as string,
    headerKpis: raw.header_kpis as Record<string, number | null>,
    miniFunnel: mapMiniFunnel(raw.mini_funnel as Record<string, unknown> | null),
    groups: ((raw.groups as Record<string, unknown>[]) ?? []).map(mapGroupOverview),
    channelList: ((raw.channel_list as Record<string, unknown>[]) ?? []).map(mapChannelOverview),
    bottlenecks: ((raw.bottlenecks as Record<string, unknown>[]) ?? []).map(mapBottleneck),
    period: (raw.period as string) ?? "last_30_days",
    lastUpdated: raw.last_updated as string | undefined,
  };
}

// ── Group Detail Mapper ─────────────────────────────────────────────────────

interface GroupDetailResponse {
  channels: ChannelMetric[];
  totals: Record<string, number>;
}

function mapGroupDetailChannel(raw: Record<string, unknown>): ChannelMetric {
  const metrics = ((raw.metrics as Record<string, unknown>[]) ?? []).map((m) => ({
    name: m.name as string,
    value: m.value as number,
    unit: m.unit as string | undefined,
    currency: m.currency as string | undefined,
    breakdown: m.breakdown as Record<string, number> | undefined,
  }));
  return {
    slug: raw.slug as string,
    name: raw.name as string,
    channelType: raw.channel_type as string,
    metrics,
    sourceLabel: raw.source_label as string,
    connected: raw.connected as boolean,
    costType: raw.cost_type as string | undefined,
    lastUpdated: raw.last_updated as string | undefined,
    stale: (raw.stale as boolean) ?? false,
    errorMessage: raw.error_message as string | undefined,
    providerName: raw.provider_name as string | undefined,
  };
}

function mapGroupDetailResponse(raw: Record<string, unknown>): GroupDetailResponse {
  return {
    channels: ((raw.channels as Record<string, unknown>[]) ?? []).map(mapGroupDetailChannel),
    totals: (raw.totals as Record<string, number>) ?? {},
  };
}

// ── Exports ─────────────────────────────────────────────────────────────────

export const stageOverviewApi = {
  getStageOverview: async (
    token: string,
    stage: string,
    period?: string,
  ): Promise<StageOverview> => {
    const params = period && period !== "last_30_days" ? `?period=${period}` : "";
    const res = await fetchClient(
      `${API_URL}/api/v1/analytics/metrics/${stage}/overview${params}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error(`Stage overview API returned ${res.status}`);
    const data = (await res.json()) as Record<string, unknown>;
    return mapStageOverview(data);
  },

  getGroupDetail: async (
    token: string,
    stage: string,
    groupKey: string,
    period?: string,
  ): Promise<GroupDetailResponse> => {
    const params = period && period !== "last_30_days" ? `?period=${period}` : "";
    const res = await fetchClient(
      `${API_URL}/api/v1/analytics/metrics/${stage}/groups/${groupKey}${params}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    );
    if (!res.ok) throw new Error(`Group detail API returned ${res.status}`);
    const data = (await res.json()) as Record<string, unknown>;
    return mapGroupDetailResponse(data);
  },
};
