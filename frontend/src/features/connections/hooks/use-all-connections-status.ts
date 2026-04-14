"use client";

import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { connectionsApi, type ConnectionStatusItem } from "@/lib/api/connections";
import { PROVIDER_TO_CHANNEL_TYPES } from "@/features/connections/config/provider-registry";

export interface ProviderStatus {
  isConnected: boolean;
  displayName?: string;
  lastSync?: string;
}

/**
 * Fetches batch connection status and returns a map of provider_id → status.
 * Maps backend channel_types back to our provider registry IDs.
 */
export function useAllConnectionsStatus() {
  const { getToken } = useAuth();

  return useQuery({
    queryKey: ["connections", "status"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      const data = await connectionsApi.getAllConnectionsStatus(token);
      return buildProviderStatusMap(data.connections);
    },
    staleTime: 30_000, // 30s — status doesn't change that fast
  });
}

function buildProviderStatusMap(
  connections: ConnectionStatusItem[],
): Record<string, ProviderStatus> {
  // Index backend connections by channel_type for fast lookup
  const byChannelType = new Map<string, ConnectionStatusItem>();
  for (const conn of connections) {
    // If multiple rows for same channel_type, prefer connected one
    const existing = byChannelType.get(conn.channel_type);
    if (!existing || (conn.is_connected && !existing.is_connected)) {
      byChannelType.set(conn.channel_type, conn);
    }
  }

  const result: Record<string, ProviderStatus> = {};

  for (const [providerId, channelTypes] of Object.entries(PROVIDER_TO_CHANNEL_TYPES)) {
    // A provider is connected if ANY of its mapped channel_types are connected
    let isConnected = false;
    let displayName: string | undefined;
    let lastSync: string | undefined;

    for (const ct of channelTypes) {
      const conn = byChannelType.get(ct);
      if (conn?.is_connected) {
        isConnected = true;
        displayName = displayName || conn.display_name || undefined;
        lastSync = lastSync || conn.last_sync || undefined;
      }
    }

    result[providerId] = { isConnected, displayName, lastSync };
  }

  return result;
}
