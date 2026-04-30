// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Mirror of backend SuggestionDTO + request/response DTOs (PR-1 PI-2 S2).
// snake_case kept as-is to match BE JSON wire format.

export type SuggestionCategory = "followup" | "action" | "clarify" | "nav";

export interface Suggestion {
  id: string; // UUID (BE serializes as string)
  label: string; // user-visible chip text (Spanish neutro LatAm, max 60 chars)
  prompt: string; // filled into the input on click
  confidence?: number; // 0..1 — now always sent from BE (D-7)
  category?: SuggestionCategory;
  source_module?: string; // provider id — needed for accept event payload (D-6 override)
}

export interface SuggestionsRequest {
  conversation_id?: string | null;
  current_route?: string | null;
  recent_message_ids?: string[];
  incomplete_fields?: string[];
}

export interface SuggestionsResponse {
  suggestions: Suggestion[];
  breakdown: Record<string, number>; // provider_id -> count (telemetría)
  latency_ms: number;
}

export interface SuggestionAcceptRequest {
  suggestion_id: string;
  conversation_id?: string | null;
  current_route?: string | null;
  category: SuggestionCategory;
  source_module: string;
  accepted_at: string; // ISO 8601 UTC — FE generates with new Date().toISOString()
}

export interface SuggestionAcceptResponse {
  ok: boolean;
}

// Legacy type kept for backward-compat — deprecated, will be removed in next iter
/** @deprecated Use SuggestionsResponse instead */
export interface SuggestionsPayload {
  conversation_id: string;
  suggestions: Suggestion[];
  generated_at: string; // ISO UTC
}
