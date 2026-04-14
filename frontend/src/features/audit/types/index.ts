export interface AuditLead {
  lead: {
    id: string;
    full_name: string;
    telegram_id: string | null;
    whatsapp_id: string | null;
    created_at: string;
  };
  last_activity: string;
}

export interface TimelineEvent {
  type: "message" | "trace";
  id: string;
  timestamp: number;
  created_at: string;
  // Message fields
  role?: string;
  content?: string;
  // Trace fields
  node_name?: string;
  execution_time_ms?: number;
  llm_summary?: {
    model: string;
    total_tokens: number;
    prompt_template?: string;
  } | null;
}

export interface TraceDetail {
  id: string;
  node_name: string;
  input_state: Record<string, unknown> | null;
  output_state: Record<string, unknown> | null;
  execution_time_ms: number;
  created_at: string;
  llm_logs: LLMLog[];
}

export interface LLMLog {
  id: string;
  model: string;
  prompt_template: string;
  prompt_rendered: string;
  response_text: string;
  tokens_input: number;
  tokens_output: number;
  metadata: Record<string, unknown>;
}

export interface LeadDetails {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  telegram_id: string | null;
  whatsapp_id: string | null;
  instagram_id: string | null;
  tiktok_id: string | null;
  profile_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
