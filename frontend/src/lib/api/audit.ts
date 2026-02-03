import { useQuery } from "@tanstack/react-query";
import { config } from "@/lib/config";
import { fetchClient } from "../http-client";
import { useAuth } from "@clerk/nextjs";

const API_BASE = `${config.api.baseUrl}/api/v1/admin`;

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
  };
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

export interface LeadDetails {
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

export function useAuditLeads() {
  const { getToken } = useAuth();
  return useQuery<AuditLead[]>({
    queryKey: ["audit", "leads"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      const res = await fetchClient(`${API_BASE}/audit/leads`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch leads");
      return res.json();
    },
  });
}

export function useLeadDetails(leadId: string | null) {
  const { getToken } = useAuth();
  return useQuery<LeadDetails>({
    queryKey: ["audit", "lead", leadId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!leadId) return null;
      const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch lead details");
      return res.json();
    },
    enabled: !!leadId,
  });
}

export function useLeadTimeline(leadId: string | null) {
  const { getToken } = useAuth();
  return useQuery<TimelineEvent[]>({
    queryKey: ["audit", "timeline", leadId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!leadId) return [];
      const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}/timeline`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch timeline");
      return res.json();
    },
    enabled: !!leadId,
  });
}

export function useTraceDetails(traceId: string | null) {
  const { getToken } = useAuth();
  return useQuery<TraceDetail>({
    queryKey: ["audit", "trace", traceId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!traceId) return null;
      const res = await fetchClient(`${API_BASE}/audit/traces/${traceId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch trace details");
      return res.json();
    },
    enabled: !!traceId,
  });
}

export async function clearLeadHistory(token: string, leadId: string) {
  const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}/history`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json();
}
