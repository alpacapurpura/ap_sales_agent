import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface StartInterviewResponse {
  session_id: string;
  conversation_id: string;
  config: Record<string, unknown>;
  initial_message: string;
}

export interface ActiveInterviewResponse {
  session_id: string;
  domain: string;
  domain_label: string;
  bloque_actual: string;
  bloques_completados: string[];
  total_bloques: number;
}

export interface InterviewStateResponse {
  session_id: string;
  mapa_global: Record<string, unknown>;
  bloque_actual: string;
  bloques_completados: string[];
  config: Record<string, unknown>;
  messages_count: number;
}

export async function startInterview(
  token: string,
  domain: string = "brand",
  entityId?: string,
): Promise<StartInterviewResponse> {
  const body: Record<string, unknown> = { domain };
  if (entityId) body.entity_id = entityId;
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  return res.json() as Promise<StartInterviewResponse>;
}

export async function getActiveInterview(token: string): Promise<ActiveInterviewResponse | null> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/active`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  if (res.status === 204) return null;
  return res.json() as Promise<ActiveInterviewResponse>;
}

export async function getInterviewState(
  token: string,
  sessionId: string,
): Promise<InterviewStateResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/state`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.json() as Promise<InterviewStateResponse>;
}

export async function pauseInterview(token: string, sessionId: string): Promise<void> {
  await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/pause`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function abandonInterview(token: string, sessionId: string): Promise<void> {
  await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/abandon`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}
