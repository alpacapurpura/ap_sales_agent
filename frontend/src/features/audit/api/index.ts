import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type { AuditLead, LeadDetails, TimelineEvent, TraceDetail } from "../types";

export const API_BASE = `${config.api.baseUrl}/api/v1/admin`;

export async function clearLeadHistory(token: string, leadId: string) {
  const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}/history`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to clear history");
  return res.json() as Promise<Record<string, unknown>>;
}

export async function fetchAuditLeads(token: string): Promise<AuditLead[]> {
  const res = await fetchClient(`${API_BASE}/audit/leads`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch leads");
  return res.json() as Promise<AuditLead[]>;
}

export async function fetchLeadDetails(token: string, leadId: string): Promise<LeadDetails> {
  const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch lead details");
  return res.json() as Promise<LeadDetails>;
}

export async function fetchLeadTimeline(token: string, leadId: string): Promise<TimelineEvent[]> {
  const res = await fetchClient(`${API_BASE}/audit/leads/${leadId}/timeline`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch timeline");
  return res.json() as Promise<TimelineEvent[]>;
}

export async function fetchTraceDetails(token: string, traceId: string): Promise<TraceDetail> {
  const res = await fetchClient(`${API_BASE}/audit/traces/${traceId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed to fetch trace details");
  return res.json() as Promise<TraceDetail>;
}
