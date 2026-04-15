import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/lib/http-client";

import { API_BASE } from "../api";

import type { AuditLead, LeadDetails, TimelineEvent, TraceDetail } from "../types";

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
