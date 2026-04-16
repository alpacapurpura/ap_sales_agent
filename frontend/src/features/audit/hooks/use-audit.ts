import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import { fetchAuditLeads, fetchLeadDetails, fetchLeadTimeline, fetchTraceDetails } from "../api";

import type { AuditLead, LeadDetails, TimelineEvent, TraceDetail } from "../types";

export function useAuditLeads() {
  const { getToken } = useAuth();
  return useQuery<AuditLead[]>({
    queryKey: ["audit", "leads"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      return fetchAuditLeads(token);
    },
  });
}

export function useLeadDetails(leadId: string | null) {
  const { getToken } = useAuth();
  return useQuery<LeadDetails | null>({
    queryKey: ["audit", "lead", leadId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!leadId) return null;
      return fetchLeadDetails(token, leadId);
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
      return fetchLeadTimeline(token, leadId);
    },
    enabled: !!leadId,
  });
}

export function useTraceDetails(traceId: string | null) {
  const { getToken } = useAuth();
  return useQuery<TraceDetail | null>({
    queryKey: ["audit", "trace", traceId],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");
      if (!traceId) return null;
      return fetchTraceDetails(token, traceId);
    },
    enabled: !!traceId,
  });
}
