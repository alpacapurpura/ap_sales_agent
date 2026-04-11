// Campaigns view types — CONTRACT.md §6.7
export type CampaignStatusFilter = "all" | "active" | "paused" | "ended";

export interface OfferCampaignsQuery {
  status?: CampaignStatusFilter;
  channel?: "meta" | "google" | "tiktok" | string;
  period_start?: string; // YYYY-MM-DD
  period_end?: string;
}

export interface OfferCampaignRow {
  id: string;
  name: string;
  channel: string;
  status: string;
  spend: number;
  leads: number;
  cpl: number | null;
  currency: string | null;
}

export interface OfferCampaignsKPIs {
  active_count: number;
  spend_7d: number;
  leads_7d: number;
  avg_cpl_7d: number | null;
  currency: string | null;
}

export interface OfferCampaignsResponse {
  offer_id: string;
  kpis: OfferCampaignsKPIs;
  campaigns: OfferCampaignRow[];
}
