import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  CloserKPIs,
  ConversationDetail,
  ConversationFilters,
  ConversationListResponse,
  DiagnoseResponse,
  FrozenConversation,
  NudgeResponse,
  ResumeResponse,
  SendMessageResponse,
  StopResponse,
} from "../types";

const BASE = `${config.api.baseUrl}/api/v1/closer-studio`;

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

// ── List ────────────────────────────────────────────────────────────────

export async function fetchConversations(
  token: string,
  filters: ConversationFilters,
  limit = 50,
  offset = 0,
): Promise<ConversationListResponse> {
  const params = new URLSearchParams();
  if (filters.temperature) params.set("temperature", filters.temperature);
  if (filters.handler_mode) params.set("handler_mode", filters.handler_mode);
  if (filters.channel) params.set("channel", filters.channel);
  if (filters.search) params.set("search", filters.search);
  params.set("limit", String(limit));
  params.set("offset", String(offset));

  const res = await fetchClient(`${BASE}/conversations?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return json(res);
}

// ── Detail ──────────────────────────────────────────────────────────────

export async function fetchConversationDetail(
  token: string,
  leadId: string,
  messageLimit = 50,
  before?: string,
): Promise<ConversationDetail> {
  const params = new URLSearchParams({ message_limit: String(messageLimit) });
  if (before) params.set("before", before);

  const res = await fetchClient(`${BASE}/conversations/${leadId}?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return json(res);
}

// ── Actions ─────────────────────────────────────────────────────────────

export async function stopAI(token: string, leadId: string): Promise<StopResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/stop`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return json(res);
}

export async function resumeAI(
  token: string,
  leadId: string,
  objective?: string,
): Promise<ResumeResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/resume`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ objective }),
  });
  return json(res);
}

export async function sendMessage(
  token: string,
  leadId: string,
  content: string,
  mode: "direct" | "instruction" = "direct",
): Promise<SendMessageResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ content, mode }),
  });
  return json(res);
}

export async function nudge(
  token: string,
  leadId: string,
  context?: string,
): Promise<NudgeResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/nudge`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ context }),
  });
  return json(res);
}

export async function reactivate(
  token: string,
  leadId: string,
  objective?: string,
): Promise<ResumeResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/reactivate`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ objective }),
  });
  return json(res);
}

export async function diagnose(token: string, leadId: string): Promise<DiagnoseResponse> {
  const res = await fetchClient(`${BASE}/conversations/${leadId}/diagnose`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  });
  return json(res);
}

// ── Frozen ──────────────────────────────────────────────────────────────

export async function fetchFrozen(token: string): Promise<FrozenConversation[]> {
  const res = await fetchClient(`${BASE}/frozen`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return json(res);
}

// ── KPIs ────────────────────────────────────────────────────────────────

export async function fetchKPIs(token: string): Promise<CloserKPIs> {
  const res = await fetchClient(`${BASE}/kpis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return json(res);
}
