import { z } from "zod";

/**
 * Mirror exacto de backend ContactFilterParams (CANONICAL_FILTER_FIELDS).
 * Arch test test_filter_params_subset valida que estos keys matchean Pydantic.
 */
export const CONTACT_FILTER_FIELDS = [
  "lifecycle_stage_in",
  "score_min",
  "score_max",
  "source_in",
  "has_email",
  "has_phone",
  "has_telegram_id",
  "has_whatsapp_id",
  "has_instagram_id",
  "has_tiktok_id",
  "created_after",
  "created_before",
  "last_activity_after",
  "last_activity_before",
  "is_inactive",
  "has_campaign_engagement",
  "country_in",
  "q",
] as const;

export type ContactFilterField = (typeof CONTACT_FILTER_FIELDS)[number];

export const lifecycleStageSchema = z.enum([
  "subscriber",
  "lead",
  "mql",
  "sql",
  "opportunity",
  "customer",
  "evangelist",
  "churned",
]);
export type LifecycleStage = z.infer<typeof lifecycleStageSchema>;

export const contactFilterParamsSchema = z.object({
  lifecycle_stage_in: z.array(lifecycleStageSchema).optional(),
  score_min: z.number().int().min(0).max(100).optional(),
  score_max: z.number().int().min(0).max(100).optional(),
  source_in: z.array(z.string()).optional(),
  has_email: z.boolean().optional(),
  has_phone: z.boolean().optional(),
  has_telegram_id: z.boolean().optional(),
  has_whatsapp_id: z.boolean().optional(),
  has_instagram_id: z.boolean().optional(),
  has_tiktok_id: z.boolean().optional(),
  created_after: z.string().datetime().optional(),
  created_before: z.string().datetime().optional(),
  last_activity_after: z.string().datetime().optional(),
  last_activity_before: z.string().datetime().optional(),
  is_inactive: z.boolean().optional(),
  has_campaign_engagement: z.boolean().optional(),
  country_in: z.array(z.string().length(2)).optional(),
  q: z.string().max(120).optional(),
});
export type ContactFilterParams = z.infer<typeof contactFilterParamsSchema>;

export interface ContactListItem {
  id: string;
  full_name: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  lifecycle_stage: LifecycleStage;
  lead_score: number;
  is_inactive: boolean;
  last_activity_at: string | null;
  lead_source: string | null;
  country: string | null;
  has_telegram_id: boolean;
  has_whatsapp_id: boolean;
  has_instagram_id: boolean;
  has_tiktok_id: boolean;
  has_email: boolean;
  has_phone: boolean;
  has_recent_campaign_engagement: boolean | null;
  created_at: string;
}

export interface ContactIdentity {
  type: string;
  value: string;
  is_primary: boolean;
  verification_status: string;
  last_seen_at: string;
}

export interface ContactDetail {
  id: string;
  full_name: string | null;
  primary_email: string | null;
  primary_phone: string | null;
  lifecycle_stage: LifecycleStage;
  lead_score: number;
  rfm_segment: string | null;
  lifetime_value: number;
  is_inactive: boolean;
  first_conversion_at: string | null;
  first_seen_at: string | null;
  last_activity_at: string | null;
  lead_source: string | null;
  lead_source_detail: string | null;
  traits: Record<string, unknown>;
  computed_traits: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
  // Lead-level optional
  lead_id: string | null;
  telegram_id: string | null;
  whatsapp_id: string | null;
  instagram_id: string | null;
  tiktok_id: string | null;
  api_id: string | null;
  fit_score: number | null;
  intent_score: number | null;
  temperature: string | null;
  is_blacklisted: boolean | null;
  last_interaction_date: string | null;
  country: string | null;
  conversation_summary: string | null;
  identities: ContactIdentity[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total_count: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

/** Slot pattern PI-3 expansion. */
export interface SelectedContactsBarAction {
  id: string;
  label: string;
  icon?: React.ReactNode;
  variant?: "default" | "secondary" | "destructive";
  onClick: (selectedIds: string[]) => void | Promise<void>;
  /** Si requires ≥1 selected (default true). */
  requiresSelection?: boolean;
}
