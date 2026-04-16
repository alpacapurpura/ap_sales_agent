"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import {
  fetchEmailDashboard,
  fetchEmailCampaigns,
  fetchEmailAutomations,
  fetchEmailAudience,
  fetchEmailHealth,
  fetchEmailGrowth,
} from "../api/mail-api";

import type {
  EmailDashboardData,
  EmailCampaignsData,
  EmailAutomationsData,
  EmailAudienceData,
  EmailHealthData,
  EmailGrowthData,
} from "../types/mail-types";
import type { MetaAdsPeriod } from "../types/metrics";

/**
 * Resolve tenant ID the same way useChannelDashboard does:
 * localStorage fallback (fetchClient also injects X-Tenant-ID automatically).
 */
function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("x-tenant-id");
}

// ---------------------------------------------------------------------------
// Panorama / Sidebar (main dashboard)
// ---------------------------------------------------------------------------

export function useMailDashboard(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailDashboardData>({
    queryKey: ["mail-dashboard", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailDashboard(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ---------------------------------------------------------------------------
// Campaigns Tab
// ---------------------------------------------------------------------------

export function useMailCampaigns(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailCampaignsData>({
    queryKey: ["mail-campaigns", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailCampaigns(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ---------------------------------------------------------------------------
// Automations Tab
// ---------------------------------------------------------------------------

export function useMailAutomations(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailAutomationsData>({
    queryKey: ["mail-automations", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailAutomations(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ---------------------------------------------------------------------------
// Audience Tab
// ---------------------------------------------------------------------------

export function useMailAudience(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailAudienceData>({
    queryKey: ["mail-audience", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailAudience(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ---------------------------------------------------------------------------
// Health Tab (Entregabilidad)
// ---------------------------------------------------------------------------

export function useMailHealth(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailHealthData>({
    queryKey: ["mail-health", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailHealth(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}

// ---------------------------------------------------------------------------
// Growth Tab (Crecimiento)
// ---------------------------------------------------------------------------

export function useMailGrowth(period: MetaAdsPeriod = "30d", enabled = true) {
  const { getToken } = useAuth();
  const tenantId = getTenantId();

  return useQuery<EmailGrowthData>({
    queryKey: ["mail-growth", tenantId, period],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchEmailGrowth(token, period);
    },
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
  });
}
