export interface Campaign {
  external_id: string;
  name: string;
  objective: string | null;
  status: string | null;
  effective_status: string | null;
  bid_strategy: string | null;
  daily_budget: number | null;
  lifetime_budget: number | null;
  budget_remaining: number | null;
  buying_type: string | null;
  start_time: string | null;
  stop_time: string | null;
  ad_sets_count: number;
  ads_count: number;
}

export interface AdSet {
  external_id: string;
  campaign_external_id: string;
  name: string;
  status: string | null;
  effective_status: string | null;
  optimization_goal: string | null;
  targeting_summary: Record<string, unknown> | null;
  learning_stage: string | null;
  daily_budget: number | null;
  ads_count: number;
}

export interface Ad {
  external_id: string;
  name: string;
  status: string | null;
  effective_status: string | null;
  creative_thumbnail_url: string | null;
  creative_title: string | null;
  creative_cta: string | null;
  preview_shareable_link: string | null;
}

export interface Recommendation {
  recommendation_type: string;
  source: string;
  title: string | null;
  body: string | null;
  importance: string | null;
  lift_estimate: string | null;
  opportunity_score: number | null;
  url: string | null;
  object_ids: string[];
}

export interface CampaignOverview {
  campaigns: Campaign[];
  recommendations: Recommendation[];
  total_campaigns: number;
  active_campaigns: number;
  last_synced: string | null;
}
