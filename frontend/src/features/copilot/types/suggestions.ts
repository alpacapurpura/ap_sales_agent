// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
// Contract §11.1 — stable interface, real engine lands later with zero FE churn.

export interface Suggestion {
  id: string; // stable UUID or "stub-*"
  label: string; // user-visible chip text (Spanish neutro LatAm)
  prompt: string; // filled into the input on click
  confidence?: number; // 0..1, future ranking; currently undefined
  category?: "followup" | "action" | "clarify" | "nav";
}

export interface SuggestionsPayload {
  conversation_id: string;
  suggestions: Suggestion[]; // ordered; max 5 chips shown
  generated_at: string; // ISO UTC
}
