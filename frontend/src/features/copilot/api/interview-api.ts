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

export async function startInterview(domain: string = "brand"): Promise<StartInterviewResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain }),
  });
  return res.json() as Promise<StartInterviewResponse>;
}

export async function getActiveInterview(): Promise<ActiveInterviewResponse | null> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/active`);
  if (res.status === 204) return null;
  return res.json() as Promise<ActiveInterviewResponse>;
}

export async function getInterviewState(sessionId: string): Promise<InterviewStateResponse> {
  const res = await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/state`);
  return res.json() as Promise<InterviewStateResponse>;
}

export async function pauseInterview(sessionId: string): Promise<void> {
  await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/pause`, {
    method: "POST",
  });
}

export async function abandonInterview(sessionId: string): Promise<void> {
  await fetchClient(`${API_URL}/api/v1/copilot/interview/${sessionId}/abandon`, {
    method: "POST",
  });
}
