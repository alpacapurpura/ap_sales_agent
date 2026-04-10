/**
 * Types for the Offer ↔ Campaign Association feature.
 *
 * Mirrors the backend DTOs in `advertising/application/dto/*`.
 * Everything is camelCase — conversion from snake_case happens in the API layer.
 */

export type TargetType = 'campaign' | 'ad_set';

export type AssociationType =
  | 'manual'
  | 'auto_landing_url'
  | 'auto_keyword'
  | 'auto_objective'
  | 'excluded_branding'
  | 'suggested';

export type AssociationConfidence = 'high' | 'medium' | 'low';

export type ExpectedMetric =
  | 'lead'
  | 'message'
  | 'purchase'
  | 'subscription'
  | 'call_booked'
  | 'form_submit';

export type HealthStatus = 'healthy' | 'needs_attention' | 'critical';

export type RecommendationSeverity = 'info' | 'warning' | 'critical';

export type RecommendationType =
  | 'create_campaign'
  | 'fix_objective'
  | 'configure_pixel'
  | 'assign_offer';

// ---------------------------------------------------------------------------
// Associations
// ---------------------------------------------------------------------------

export interface Association {
  id: string;
  tenantId: string;
  targetType: TargetType;
  targetExternalId: string;
  offerId: string | null;
  offerName: string | null;
  offerArchetype: string | null;
  associationType: AssociationType;
  confidence: AssociationConfidence | null;
  notes: string | null;
  createdAt: string;
  updatedAt: string | null;
}

export interface AssociationCreatePayload {
  targetType: TargetType;
  targetExternalId: string;
  offerId: string | null;
  associationType: 'manual' | 'excluded_branding';
  notes?: string | null;
}

export interface AssociationSuggestion {
  targetType: TargetType;
  targetExternalId: string;
  targetName: string;
  suggestedOfferId: string;
  suggestedOfferName: string;
  associationType: AssociationType;
  confidence: AssociationConfidence;
  reason: string;
}

export interface AssociationsFilters {
  targetType?: TargetType;
  offerId?: string;
}

// ---------------------------------------------------------------------------
// Health Check
// ---------------------------------------------------------------------------

export interface CampaignHealth {
  externalId: string;
  name: string;
  objective: string | null;
  objectiveLabelEs: string;
  status: string | null;
  offerAssociation: Association | null;
  expectedOutcomeEs: string;
  hasIssue: boolean;
  issueText: string | null;
}

export interface OfferCoverage {
  offerId: string;
  offerName: string;
  archetype: string;
  expectedMetric: ExpectedMetric;
  expectedMetricLabelEs: string;
  hasActiveCampaign: boolean;
  associatedTargets: Association[];
}

export interface UnassignedTarget {
  targetType: TargetType;
  externalId: string;
  name: string;
  objective: string | null;
  status: string | null;
}

export interface Recommendation {
  type: RecommendationType;
  severity: RecommendationSeverity;
  title: string;
  body: string;
  actionLabel: string;
  actionUrl: string | null;
  relatedOfferId: string | null;
  relatedTargetId: string | null;
}

export interface MetaHealthCheck {
  overallStatus: HealthStatus;
  activeCampaigns: CampaignHealth[];
  offersCoverage: OfferCoverage[];
  unassignedTargets: UnassignedTarget[];
  recommendations: Recommendation[];
  summaryText: string;
}

// ---------------------------------------------------------------------------
// Metrics by Offer
// ---------------------------------------------------------------------------

export interface OfferTimeSeriesPoint {
  date: string;
  spend: number;
  primaryResult: number;
}

export interface OfferMetrics {
  offerId: string;
  offerName: string;
  archetype: string;
  expectedMetric: ExpectedMetric;
  expectedMetricLabelEs: string;
  totalSpend: number;
  currency: string;
  primaryResultCount: number;
  primaryCostPerResult: number | null;
  primaryMetricName: string;
  primaryMetricUnit: 'currency' | 'count' | 'ratio';
  roas: number | null;
  secondaryMetrics: Record<string, number>;
  timeseries: OfferTimeSeriesPoint[];
  metricUnavailableReason: string | null;
}

export interface UnassignedAggregate {
  targetCount: number;
  totalSpend: number;
  impressions: number;
  clicks: number;
}

export interface BrandingAggregate {
  targetCount: number;
  totalSpend: number;
  reach: number;
  impressions: number;
}

export interface MetricsByOffer {
  period: string;
  startDate: string;
  endDate: string;
  currency: string | null;
  offers: OfferMetrics[];
  unassigned: UnassignedAggregate;
  brandingOnly: BrandingAggregate;
}

// ---------------------------------------------------------------------------
// Campaign Templates (read-only base for future Action Trigger)
// ---------------------------------------------------------------------------

export interface AdCampaignTemplate {
  id: string;
  offerArchetype: string;
  offerOnboardingAction: string | null;
  offerIsLeadMagnet: boolean | null;
  name: string;
  description: string;
  recommendedObjective: string;
  recommendedObjectiveLabelEs: string;
  recommendedOptimizationGoal: string | null;
  recommendedDestinationType: string | null;
  structureHints: Record<string, unknown>;
  priority: number;
}

// ---------------------------------------------------------------------------
// Chart modes for the Inversión chart
// ---------------------------------------------------------------------------

/**
 * Chart mode drives:
 *  - the metric shown on the right Y axis
 *  - the bar-color rule (break-even vs goal-based)
 *  - the tooltip labels
 *  - the narrative subtitle
 *
 * `mixed` = "Todas las offers" — no common secondary metric, just spend bars.
 */
export type InversionChartMode =
  | 'traffic'
  | 'leads'
  | 'messages'
  | 'purchases'
  | 'subscriptions'
  | 'calls'
  | 'forms'
  | 'mixed';

/**
 * Map an offer's expected metric to the chart mode.
 */
export function expectedMetricToChartMode(metric: ExpectedMetric): InversionChartMode {
  switch (metric) {
    case 'lead':
      return 'leads';
    case 'message':
      return 'messages';
    case 'purchase':
      return 'purchases';
    case 'subscription':
      return 'subscriptions';
    case 'call_booked':
      return 'calls';
    case 'form_submit':
      return 'forms';
  }
}

/**
 * Emoji icon for an offer archetype — used in chips and dropdowns.
 */
export function archetypeEmoji(archetype: string | null | undefined): string {
  const upper = (archetype ?? '').toUpperCase();
  if (upper === 'PRODUCTO') return '🧲';
  if (upper === 'PROGRAMA') return '📚';
  if (upper === 'SERVICIO') return '⭐';
  if (upper === 'MEMBRESIA') return '👥';
  if (upper === 'EXPERIENCIA') return '🎟️';
  return '📦';
}
