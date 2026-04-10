/**
 * TypeScript types for the Email Marketing dashboard (MailerLite integration).
 * Matches backend DTOs from analytics/api/metrics.py (camelCase frontend convention).
 */

import type { MetricKpiData, MetricTimeSeries, FunnelStep } from './metrics';

// ---------------------------------------------------------------------------
// Health Score
// ---------------------------------------------------------------------------

export interface EmailHealthSubScore {
  area: string; // engagement | entregabilidad | crecimiento | contenido
  label: string;
  score: number;
  color: string; // green | yellow | red
}

export interface EmailHealthScore {
  total: number;
  subScores: EmailHealthSubScore[];
}

// ---------------------------------------------------------------------------
// Campaign Summary (sidebar best/worst)
// ---------------------------------------------------------------------------

export interface EmailCampaignSummary {
  campaignName: string;
  campaignSubject: string | null;
  campaignType: string;
  sentCount: number;
  openRate: number;
  clickToOpenRate: number;
  sentDate: string | null;
}

// ---------------------------------------------------------------------------
// Campaigns vs Automations comparison
// ---------------------------------------------------------------------------

export interface CampaignsVsAutomations {
  campaignsSent: number;
  campaignsOpenRate: number;
  campaignsClickRate: number;
  campaignsCtor: number;
  campaignsUnsubs: number;
  automationsSent: number;
  automationsOpenRate: number;
  automationsClickRate: number;
  automationsCtor: number;
  automationsUnsubs: number;
}

// ---------------------------------------------------------------------------
// Main Dashboard (sidebar + panorama tab)
// ---------------------------------------------------------------------------

export interface EmailDashboardData {
  channelSlug: string;
  channelName: string;
  providerName: string | null;
  period: string;
  healthScore: EmailHealthScore;
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
  funnel: FunnelStep[];
  bestCampaign: EmailCampaignSummary | null;
  worstCampaign: EmailCampaignSummary | null;
  campaignsVsAutomations: CampaignsVsAutomations | null;
}

// ---------------------------------------------------------------------------
// Campaigns Tab
// ---------------------------------------------------------------------------

export interface EmailCampaign {
  campaignId: string;
  campaignName: string;
  campaignSubject: string | null;
  campaignType: string;
  sentDate: string | null;
  emailsSent: number;
  openRate: number;
  clickRate: number;
  clickToOpenRate: number;
  bounceRate: number;
  unsubscribes: number;
  uniqueOpens: number;
  uniqueClicks: number;
}

export interface EmailTypePerformance {
  campaignType: string;
  campaignCount: number;
  totalSent: number;
  avgOpenRate: number;
  avgCtor: number;
  totalUnsubs: number;
  rankLabel: string;
}

export interface EmailCampaignsData {
  period: string;
  typePerformance: EmailTypePerformance[];
  campaigns: EmailCampaign[];
  topSubjects: EmailCampaignSummary[];
}

// ---------------------------------------------------------------------------
// Automations Tab
// ---------------------------------------------------------------------------

export interface EmailAutomation {
  automationId: string;
  name: string;
  automationType: string;
  status: string;
  activeSubscribers: number;
  completed: number;
  emailsSent: number;
  openRate: number;
  clickRate: number;
  completionRate: number;
}

export interface EmailAutomationsData {
  period: string;
  kpis: MetricKpiData[];
  automations: EmailAutomation[];
}

// ---------------------------------------------------------------------------
// Audience Tab
// ---------------------------------------------------------------------------

export interface EmailEngagementSegment {
  segmentName: string;
  label: string;
  count: number;
  percentage: number;
  openRate: number;
  clickRate: number;
  ctor: number;
  avgDaysInactive: number | null;
  recommendedAction: string;
}

export interface SegmentTypeMatrixCell {
  segmentName: string;
  campaignType: string;
  openRate: number;
}

export interface EmailSourcePerformance {
  source: string;
  label: string;
  subscriberCount: number;
  percentage: number;
  openRate: number;
  clickRate: number;
  championsPct: number;
}

export interface EngagementDecay {
  periodLabel: string;
  openRate: number;
}

export interface ActivityHeatmapCell {
  dayOfWeek: number;
  hourBlock: string;
  openRate: number;
}

export interface EmailAudienceData {
  period: string;
  segments: EmailEngagementSegment[];
  segmentTypeMatrix: SegmentTypeMatrixCell[];
  sources: EmailSourcePerformance[];
  engagementDecay: EngagementDecay[];
  activityHeatmap: ActivityHeatmapCell[];
}

// ---------------------------------------------------------------------------
// Health Tab (Entregabilidad)
// ---------------------------------------------------------------------------

export interface BounceBreakdown {
  hardBounces: number;
  softBounces: number;
  hardBounceRate: number;
  softBounceRate: number;
  totalDelivered: number;
}

export interface EmailHealthData {
  period: string;
  campaignsCount: number;
  healthScore: EmailHealthScore;
  kpis: MetricKpiData[];
  bounceBreakdown: BounceBreakdown;
  timeSeries: MetricTimeSeries[];
  alerts: string[];
}

// ---------------------------------------------------------------------------
// Growth Tab (Crecimiento)
// ---------------------------------------------------------------------------

export interface EmailGrowthData {
  period: string;
  kpis: MetricKpiData[];
  timeSeries: MetricTimeSeries[];
  sources: EmailSourcePerformance[];
  retentionCurve: EngagementDecay[];
}
