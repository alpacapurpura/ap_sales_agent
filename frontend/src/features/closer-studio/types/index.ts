// ── Conversation Types ──────────────────────────────────────────────────

export type HandlerMode = "ai" | "human";
export type Temperature = "cold" | "warm" | "hot";
export type InputMode = "direct" | "instruction";

export interface ConversationListItem {
  lead_id: string;
  customer_profile_id: string | null;
  display_name: string;
  channel: string | null;
  temperature: Temperature | null;
  lead_score: number;
  handler_mode: HandlerMode;
  funnel_stage: string;
  pipeline_stage: string | null;
  last_message_preview: string | null;
  last_message_at: string | null;
  unread_count: number;
  avatar_url: string | null;
  is_frozen: boolean;
}

export interface ConversationListResponse {
  conversations: ConversationListItem[];
  total: number;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  sender_source: "auto" | "human_direct" | "human_instruction";
  channel: string | null;
  created_at: string | null;
  metadata: Record<string, unknown> | null;
}

export interface ConversationDetail {
  lead_id: string;
  display_name: string;
  channel: string | null;
  temperature: Temperature | null;
  lead_score: number;
  handler_mode: HandlerMode;
  funnel_stage: string;
  pipeline_stage: string | null;
  paused_at: string | null;
  unread_count: number;
  qualification_answers: Record<string, unknown> | null;
  buying_signals: Array<Record<string, unknown>>;
  lead_data: Record<string, unknown> | null;
  customer_profile_id: string | null;
  avatar_url: string | null;
  messages: MessageItem[];
  total_messages: number;
}

// ── Action Types ────────────────────────────────────────────────────────

export interface StopResponse {
  lead_id: string;
  handler_mode: HandlerMode;
  paused_at: string | null;
}

export interface ResumeResponse {
  lead_id: string;
  handler_mode: HandlerMode;
  resume_objective: string | null;
}

export interface SendMessageResponse {
  message_id: string;
  content: string;
  mode: string;
  sent_to_channel: boolean;
}

export interface NudgeResponse {
  message_id: string | null;
  content: string;
  sent_to_channel: boolean;
}

export interface DiagnoseResponse {
  lead_id: string;
  diagnosis: Record<string, unknown>;
  generated_at: string;
}

// ── Frozen ──────────────────────────────────────────────────────────────

export interface FrozenConversation {
  lead_id: string;
  display_name: string;
  channel: string | null;
  temperature: Temperature | null;
  lead_score: number;
  funnel_stage: string;
  frozen_at: string | null;
  frozen_reason: string | null;
  frozen_diagnosis: Record<string, unknown> | null;
  last_message_at: string | null;
  last_message_preview: string | null;
  avatar_url: string | null;
}

// ── KPIs ────────────────────────────────────────────────────────────────

export interface CloserKPIs {
  total_active: number;
  handled_by_ai: number;
  handled_by_human: number;
  frozen_count: number;
  hot_count: number;
  warm_count: number;
  cold_count: number;
  avg_lead_score: number;
  unread_total: number;
}

// ── Filters ─────────────────────────────────────────────────────────────

export interface ConversationFilters {
  temperature: Temperature | null;
  handler_mode: HandlerMode | null;
  channel: string | null;
  search: string;
}
