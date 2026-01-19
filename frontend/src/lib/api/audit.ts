import { useQuery } from "@tanstack/react-query";
import { config } from "../config";

const API_BASE = `${config.api.baseUrl}/api/v1/admin`;

export interface AuditUser {
  user: {
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
}

export interface TraceDetail {
  id: string;
  node_name: string;
  input_state: any;
  output_state: any;
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
  metadata: any;
}

export interface UserDetails {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  telegram_id: string | null;
  whatsapp_id: string | null;
  instagram_id: string | null;
  tiktok_id: string | null;
  profile_data: any;
  created_at: string;
  updated_at: string;
}

export function useAuditUsers() {
  return useQuery<AuditUser[]>({
    queryKey: ["audit", "users"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/audit/users`);
      if (!res.ok) throw new Error("Failed to fetch users");
      return res.json();
    },
  });
}

export function useUserDetails(userId: string | null) {
  return useQuery<UserDetails>({
    queryKey: ["audit", "user", userId],
    queryFn: async () => {
      if (!userId) return null;
      const res = await fetch(`${API_BASE}/audit/users/${userId}`);
      if (!res.ok) throw new Error("Failed to fetch user details");
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useUserTimeline(userId: string | null) {
  return useQuery<TimelineEvent[]>({
    queryKey: ["audit", "timeline", userId],
    queryFn: async () => {
      if (!userId) return [];
      const res = await fetch(`${API_BASE}/audit/users/${userId}/timeline`);
      if (!res.ok) throw new Error("Failed to fetch timeline");
      return res.json();
    },
    enabled: !!userId,
  });
}

export function useTraceDetails(traceId: string | null) {
  return useQuery<TraceDetail>({
    queryKey: ["audit", "trace", traceId],
    queryFn: async () => {
      if (!traceId) return null;
      const res = await fetch(`${API_BASE}/audit/traces/${traceId}`);
      if (!res.ok) throw new Error("Failed to fetch trace details");
      return res.json();
    },
    enabled: !!traceId,
  });
}
