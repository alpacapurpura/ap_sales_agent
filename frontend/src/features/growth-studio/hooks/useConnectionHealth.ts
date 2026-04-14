"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";

import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";

const API_URL = config.api.baseUrl;

export interface ConnectionHealthData {
  status: "healthy" | "expiring_soon" | "expired" | "not_connected";
  channelSlug: string;
  expiresAt: string | null;
  message: string;
}

interface ConnectionHealthResponse {
  status: string;
  channel_slug: string;
  expires_at: string | null;
  message: string;
}

function mapResponse(raw: ConnectionHealthResponse): ConnectionHealthData {
  return {
    status: raw.status as ConnectionHealthData["status"],
    channelSlug: raw.channel_slug,
    expiresAt: raw.expires_at,
    message: raw.message,
  };
}

export async function fetchConnectionHealth(
  token: string,
  channelSlug: string,
): Promise<ConnectionHealthData> {
  const url = `${API_URL}/api/v1/connections/${channelSlug}/health`;
  const res = await fetchClient(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Connection health API returned ${res.status}`);
  const json: ConnectionHealthResponse = await res.json();
  return mapResponse(json);
}

export function useConnectionHealth(channelSlug: string, enabled = true) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== "undefined" ? localStorage.getItem("x-tenant-id") : null;

  return useQuery<ConnectionHealthData>({
    queryKey: ["connection-health", tenantId, channelSlug],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return fetchConnectionHealth(token, channelSlug);
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}
