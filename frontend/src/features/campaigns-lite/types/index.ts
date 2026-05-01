import { z } from "zod";

// ---------------------------------------------------------------------------
// Enums (mirror backend enums)
// ---------------------------------------------------------------------------

export const campaignTypeSchema = z.enum([
  "AGENT_CONVERSATION",
  "BROADCAST",
  "DRIP",
  "RETARGETING",
]);
export type CampaignType = z.infer<typeof campaignTypeSchema>;

export const campaignStatusSchema = z.enum([
  "DRAFT",
  "SCHEDULED",
  "RUNNING",
  "PAUSED",
  "COMPLETED",
  "CANCELLED",
]);
export type CampaignStatus = z.infer<typeof campaignStatusSchema>;

// ---------------------------------------------------------------------------
// Response shapes (camelCase-aligned mirror of Pydantic DTOs)
// ---------------------------------------------------------------------------

export interface CampaignResponse {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  campaign_type: CampaignType;
  status: CampaignStatus;
  segment_id: string | null;
  channel_priority: string[];
  offer_id: string | null;
  brand_summary_id: string | null;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string | null;
  scheduled_for: string | null;
  launched_at: string | null;
}

export interface CampaignStatsResponse {
  campaign_id: string;
  total_tasks: number;
  sent_count: number;
  responded_count: number;
  converted_count: number;
  response_rate: number;
  conversion_rate: number;
  /** Currency from master-data. NEVER hardcode USD. */
  currency: string | null;
}

// ---------------------------------------------------------------------------
// Form schemas (Zod)
// ---------------------------------------------------------------------------

/** Usado por CreateSegmentDialog. */
export const createSegmentFormSchema = z.object({
  name: z.string().min(1, "El nombre es requerido").max(128, "Máximo 128 caracteres"),
  description: z.string().max(1000, "Máximo 1000 caracteres").optional(),
});
export type CreateSegmentFormValues = z.infer<typeof createSegmentFormSchema>;

/** Usado por CampaignNewClient. */
export const createCampaignFormSchema = z.object({
  name: z.string().min(1, "El nombre es requerido").max(255, "Máximo 255 caracteres"),
  description: z.string().max(2000, "Máximo 2000 caracteres").optional(),
  /** Vacío → campaña en DRAFT, sin schedule. Con fecha → POST /schedule. */
  scheduled_for: z.string().optional(),
});
export type CreateCampaignFormValues = z.infer<typeof createCampaignFormSchema>;
