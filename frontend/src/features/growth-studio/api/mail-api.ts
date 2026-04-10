/**
 * API client for the Email Marketing dashboard endpoints.
 * Maps snake_case backend responses to camelCase frontend types.
 */

import { fetchClient } from '@/lib/http-client';
import { config } from '@/lib/config';
import type { MetaAdsPeriod } from '../types/metrics';
import type {
  EmailDashboardData,
  EmailCampaignsData,
  EmailAutomationsData,
  EmailAudienceData,
  EmailHealthData,
  EmailGrowthData,
  EmailHealthScore,
  EmailHealthSubScore,
  EmailCampaignSummary,
  CampaignsVsAutomations,
  EmailCampaign,
  EmailTypePerformance,
  EmailAutomation,
  AutomationStep,
  EmailEngagementSegment,
  SegmentTypeMatrixCell,
  EmailSourcePerformance,
  EngagementDecay,
  ActivityHeatmapCell,
  BounceBreakdown,
} from '../types/mail-types';
import type { MetricKpiData, MetricTimeSeries, FunnelStep } from '../types/metrics';

const API_URL = config.api.baseUrl;

// ---------------------------------------------------------------------------
// Shared mappers (snake_case -> camelCase)
// ---------------------------------------------------------------------------

function mapKpi(raw: Record<string, unknown>): MetricKpiData {
  return {
    metricName: raw.metric_name as string,
    displayName: raw.display_name as string,
    currentValue: raw.current_value as number,
    previousValue: (raw.previous_value as number | null) ?? null,
    deltaPct: (raw.delta_percent as number | null) ?? null,
    deltaAbsolute: (raw.delta_absolute as number | null) ?? null,
    unit: raw.unit as string,
    currency: (raw.currency as string) ?? undefined,
    higherIsBetter: raw.higher_is_better as boolean,
    benchmark: raw.benchmark ? (raw.benchmark as MetricKpiData['benchmark']) : null,
  };
}

function mapTimeSeries(raw: Record<string, unknown>): MetricTimeSeries {
  const dp = raw.data_points as Array<{ date: string; value: number }>;
  return {
    metricName: raw.metric_name as string,
    displayName: raw.display_name as string,
    unit: raw.unit as string,
    dataPoints: dp,
  };
}

function mapFunnelStep(raw: Record<string, unknown>): FunnelStep {
  return {
    label: raw.label as string,
    metricName: raw.metric_name as string,
    value: raw.value as number,
    conversionRate: (raw.conversion_rate_from_previous as number | null) ?? null,
  };
}

function mapHealthSubScore(raw: Record<string, unknown>): EmailHealthSubScore {
  return {
    area: raw.area as string,
    label: raw.label as string,
    score: raw.score as number,
    color: raw.color as string,
  };
}

function mapHealthScore(raw: Record<string, unknown>): EmailHealthScore {
  const subs = raw.sub_scores as Array<Record<string, unknown>>;
  return {
    total: raw.total as number,
    subScores: subs.map(mapHealthSubScore),
  };
}

function mapCampaignSummary(raw: Record<string, unknown>): EmailCampaignSummary {
  return {
    campaignName: raw.campaign_name as string,
    campaignSubject: (raw.campaign_subject as string | null) ?? null,
    campaignType: raw.campaign_type as string,
    sentCount: raw.sent_count as number,
    openRate: raw.open_rate as number,
    clickToOpenRate: raw.click_to_open_rate as number,
    sentDate: (raw.sent_date as string | null) ?? null,
  };
}

function mapCampaignsVsAutomations(raw: Record<string, unknown>): CampaignsVsAutomations {
  return {
    campaignsSent: raw.campaigns_sent as number,
    campaignsOpenRate: raw.campaigns_open_rate as number,
    campaignsClickRate: raw.campaigns_click_rate as number,
    campaignsCtor: raw.campaigns_ctor as number,
    campaignsUnsubs: raw.campaigns_unsubs as number,
    automationsSent: raw.automations_sent as number,
    automationsOpenRate: raw.automations_open_rate as number,
    automationsClickRate: raw.automations_click_rate as number,
    automationsCtor: raw.automations_ctor as number,
    automationsUnsubs: raw.automations_unsubs as number,
  };
}

// ---------------------------------------------------------------------------
// Dashboard (panorama + sidebar)
// ---------------------------------------------------------------------------

function mapEmailDashboardResponse(raw: Record<string, unknown>): EmailDashboardData {
  const kpis = raw.kpis as Array<Record<string, unknown>>;
  const ts = raw.time_series as Array<Record<string, unknown>>;
  const funnel = raw.funnel as Array<Record<string, unknown>>;
  const health = raw.health_score as Record<string, unknown>;
  const best = raw.best_campaign as Record<string, unknown> | null;
  const worst = raw.worst_campaign as Record<string, unknown> | null;
  const cva = raw.campaigns_vs_automations as Record<string, unknown> | null;

  return {
    channelSlug: raw.channel_slug as string,
    channelName: raw.channel_name as string,
    providerName: (raw.provider_name as string | null) ?? null,
    period: raw.period as string,
    healthScore: mapHealthScore(health),
    kpis: kpis.map(mapKpi),
    timeSeries: ts.map(mapTimeSeries),
    funnel: funnel.map(mapFunnelStep),
    bestCampaign: best ? mapCampaignSummary(best) : null,
    worstCampaign: worst ? mapCampaignSummary(worst) : null,
    campaignsVsAutomations: cva ? mapCampaignsVsAutomations(cva) : null,
  };
}

export async function fetchEmailDashboard(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailDashboardData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/dashboard?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email dashboard fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailDashboardResponse(json);
}

// ---------------------------------------------------------------------------
// Campaigns Tab
// ---------------------------------------------------------------------------

function mapEmailCampaign(raw: Record<string, unknown>): EmailCampaign {
  return {
    campaignId: raw.campaign_id as string,
    campaignName: raw.campaign_name as string,
    campaignSubject: (raw.campaign_subject as string | null) ?? null,
    campaignType: raw.campaign_type as string,
    sentDate: (raw.sent_date as string | null) ?? null,
    emailsSent: raw.emails_sent as number,
    openRate: raw.open_rate as number,
    clickRate: raw.click_rate as number,
    clickToOpenRate: raw.click_to_open_rate as number,
    bounceRate: raw.bounce_rate as number,
    unsubscribes: raw.unsubscribes as number,
    uniqueOpens: raw.unique_opens as number,
    uniqueClicks: raw.unique_clicks as number,
  };
}

function mapTypePerformance(raw: Record<string, unknown>): EmailTypePerformance {
  return {
    campaignType: raw.campaign_type as string,
    campaignCount: raw.campaign_count as number,
    totalSent: raw.total_sent as number,
    avgOpenRate: raw.avg_open_rate as number,
    avgCtor: raw.avg_ctor as number,
    totalUnsubs: raw.total_unsubs as number,
    rankLabel: raw.rank_label as string,
  };
}

function mapEmailCampaignsResponse(raw: Record<string, unknown>): EmailCampaignsData {
  const types = raw.type_performance as Array<Record<string, unknown>>;
  const campaigns = raw.campaigns as Array<Record<string, unknown>>;
  const subjects = raw.top_subjects as Array<Record<string, unknown>>;

  return {
    period: raw.period as string,
    typePerformance: types.map(mapTypePerformance),
    campaigns: campaigns.map(mapEmailCampaign),
    topSubjects: subjects.map(mapCampaignSummary),
  };
}

export async function fetchEmailCampaigns(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailCampaignsData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/campaigns?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email campaigns fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailCampaignsResponse(json);
}

// ---------------------------------------------------------------------------
// Automations Tab
// ---------------------------------------------------------------------------

function mapAutomationStep(raw: Record<string, unknown>): AutomationStep {
  return {
    stepId: raw.step_id as string,
    stepNumber: raw.step_number as number,
    type: raw.type as 'email' | 'delay' | 'condition',
    subject: (raw.subject as string | null) ?? null,
    fromName: (raw.from_name as string | null) ?? null,
    emailsSent: (raw.emails_sent as number) ?? 0,
    uniqueOpens: (raw.unique_opens as number) ?? 0,
    openRate: (raw.open_rate as number) ?? 0,
    uniqueClicks: (raw.unique_clicks as number) ?? 0,
    clickRate: (raw.click_rate as number) ?? 0,
    unsubscribes: (raw.unsubscribes as number) ?? 0,
    bounces: (raw.bounces as number) ?? 0,
    screenshotUrl: (raw.screenshot_url as string | null) ?? null,
    previewUrl: (raw.preview_url as string | null) ?? null,
    delayValue: (raw.delay_value as number | null) ?? null,
    delayUnit: (raw.delay_unit as string | null) ?? null,
  };
}

function mapEmailAutomation(raw: Record<string, unknown>): EmailAutomation {
  const steps = (raw.steps as Array<Record<string, unknown>> | undefined) ?? [];
  return {
    automationId: raw.automation_id as string,
    name: raw.name as string,
    automationType: raw.automation_type as string,
    status: raw.status as string,
    activeSubscribers: raw.active_subscribers as number,
    completed: raw.completed as number,
    emailsSent: raw.emails_sent as number,
    openRate: raw.open_rate as number,
    clickRate: raw.click_rate as number,
    clickToOpenRate: (raw.click_to_open_rate as number) ?? 0,
    completionRate: raw.completion_rate as number,
    unsubscribes: (raw.unsubscribes as number) ?? 0,
    steps: steps.map(mapAutomationStep),
  };
}

function mapEmailAutomationsResponse(raw: Record<string, unknown>): EmailAutomationsData {
  const kpis = raw.kpis as Array<Record<string, unknown>>;
  const automations = raw.automations as Array<Record<string, unknown>>;

  return {
    period: raw.period as string,
    kpis: kpis.map(mapKpi),
    automations: automations.map(mapEmailAutomation),
  };
}

export async function fetchEmailAutomations(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailAutomationsData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/automations?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email automations fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailAutomationsResponse(json);
}

// ---------------------------------------------------------------------------
// Audience Tab
// ---------------------------------------------------------------------------

function mapEngagementSegment(raw: Record<string, unknown>): EmailEngagementSegment {
  return {
    segmentName: raw.segment_name as string,
    label: raw.label as string,
    count: raw.count as number,
    percentage: raw.percentage as number,
    openRate: raw.open_rate as number,
    clickRate: raw.click_rate as number,
    ctor: raw.ctor as number,
    avgDaysInactive: (raw.avg_days_inactive as number | null) ?? null,
    recommendedAction: raw.recommended_action as string,
  };
}

function mapSegmentTypeMatrixCell(raw: Record<string, unknown>): SegmentTypeMatrixCell {
  return {
    segmentName: raw.segment_name as string,
    campaignType: raw.campaign_type as string,
    openRate: raw.open_rate as number,
  };
}

function mapSourcePerformance(raw: Record<string, unknown>): EmailSourcePerformance {
  return {
    source: raw.source as string,
    label: raw.label as string,
    subscriberCount: raw.subscriber_count as number,
    percentage: raw.percentage as number,
    openRate: raw.open_rate as number,
    clickRate: raw.click_rate as number,
    championsPct: raw.champions_pct as number,
  };
}

function mapEngagementDecay(raw: Record<string, unknown>): EngagementDecay {
  return {
    periodLabel: raw.period_label as string,
    openRate: raw.open_rate as number,
  };
}

function mapActivityHeatmapCell(raw: Record<string, unknown>): ActivityHeatmapCell {
  return {
    dayOfWeek: raw.day_of_week as number,
    hourBlock: raw.hour_block as string,
    openRate: raw.open_rate as number,
  };
}

function mapEmailAudienceResponse(raw: Record<string, unknown>): EmailAudienceData {
  const segments = raw.segments as Array<Record<string, unknown>>;
  const matrix = raw.segment_type_matrix as Array<Record<string, unknown>>;
  const sources = raw.sources as Array<Record<string, unknown>>;
  const decay = raw.engagement_decay as Array<Record<string, unknown>>;
  const heatmap = raw.activity_heatmap as Array<Record<string, unknown>>;

  return {
    period: raw.period as string,
    segments: segments.map(mapEngagementSegment),
    segmentTypeMatrix: matrix.map(mapSegmentTypeMatrixCell),
    sources: sources.map(mapSourcePerformance),
    engagementDecay: decay.map(mapEngagementDecay),
    activityHeatmap: heatmap.map(mapActivityHeatmapCell),
  };
}

export async function fetchEmailAudience(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailAudienceData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/audience?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email audience fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailAudienceResponse(json);
}

// ---------------------------------------------------------------------------
// Health Tab (Entregabilidad)
// ---------------------------------------------------------------------------

function mapBounceBreakdown(raw: Record<string, unknown>): BounceBreakdown {
  return {
    hardBounces: raw.hard_bounces as number,
    softBounces: raw.soft_bounces as number,
    hardBounceRate: raw.hard_bounce_rate as number,
    softBounceRate: raw.soft_bounce_rate as number,
    totalDelivered: raw.total_delivered as number,
  };
}

function mapEmailHealthResponse(raw: Record<string, unknown>): EmailHealthData {
  const health = raw.health_score as Record<string, unknown>;
  const kpis = raw.kpis as Array<Record<string, unknown>>;
  const bounce = raw.bounce_breakdown as Record<string, unknown>;
  const ts = raw.time_series as Array<Record<string, unknown>>;
  const alerts = raw.alerts as string[];

  return {
    period: raw.period as string,
    campaignsCount: (raw.campaigns_count as number) ?? 0,
    healthScore: mapHealthScore(health),
    kpis: kpis.map(mapKpi),
    bounceBreakdown: mapBounceBreakdown(bounce),
    timeSeries: ts.map(mapTimeSeries),
    alerts,
  };
}

export async function fetchEmailHealth(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailHealthData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/health?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email health fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailHealthResponse(json);
}

// ---------------------------------------------------------------------------
// Growth Tab (Crecimiento)
// ---------------------------------------------------------------------------

function mapEmailGrowthResponse(raw: Record<string, unknown>): EmailGrowthData {
  const kpis = raw.kpis as Array<Record<string, unknown>>;
  const ts = raw.time_series as Array<Record<string, unknown>>;
  const sources = raw.sources as Array<Record<string, unknown>>;
  const retention = raw.retention_curve as Array<Record<string, unknown>>;

  return {
    period: raw.period as string,
    kpis: kpis.map(mapKpi),
    timeSeries: ts.map(mapTimeSeries),
    sources: sources.map(mapSourcePerformance),
    retentionCurve: retention.map(mapEngagementDecay),
  };
}

export async function fetchEmailGrowth(
  token: string,
  period: MetaAdsPeriod = '30d',
): Promise<EmailGrowthData> {
  const url = `${API_URL}/api/v1/analytics/metrics/email/growth?period=${period}`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Email growth fetch failed: ${res.status}`);
  const json: Record<string, unknown> = await res.json();
  return mapEmailGrowthResponse(json);
}
