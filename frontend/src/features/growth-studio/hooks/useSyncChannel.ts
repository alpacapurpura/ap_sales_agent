"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

const API_URL = config.api.baseUrl;

interface SyncChannelResult {
  status: string;
  run_id: string;
  provider: string;
  channel_slug: string;
}

interface SyncChannelError {
  detail: string;
  remaining_minutes?: number;
}

/**
 * Hook to sync a single channel's metrics via the refresh endpoint.
 * Uses fetchClient (with X-Tenant-ID) + Bearer auth.
 * Invalidates relevant queries on success so the UI refreshes.
 */
export function useSyncChannel(channelSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation<SyncChannelResult, SyncChannelError>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw { detail: "No auth token" } as SyncChannelError;

      const res = await fetchClient(
        `${API_URL}/api/v1/analytics/metrics/attraction/refresh/${channelSlug}`,
        {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      if (res.status === 429) {
        const errData = await res.json().catch(() => ({}));
        const err: SyncChannelError = {
          detail: errData.detail ?? "Rate limited",
          remaining_minutes: errData.remaining_minutes,
        };
        throw err;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw { detail: errData.detail ?? `Sync failed (${res.status})` } as SyncChannelError;
      }

      return res.json();
    },
    onSuccess: () => {
      // Invalidate channel-specific dashboard queries
      void queryClient.invalidateQueries({ queryKey: ["channel-dashboard"] });
      // Invalidate stage-level queries so ChannelRow data refreshes
      void queryClient.invalidateQueries({ queryKey: ["attraction-detail"] });
      void queryClient.invalidateQueries({ queryKey: ["capture-detail"] });
      void queryClient.invalidateQueries({ queryKey: ["nurture-detail"] });
      void queryClient.invalidateQueries({ queryKey: ["bowties-summary"] });
      // Invalidate campaign data (for Meta Ads)
      void queryClient.invalidateQueries({ queryKey: ["campaigns"] });
      void queryClient.invalidateQueries({ queryKey: ["ad-performance"] });
    },
  });

  // Auto-reset result/error after 10s
  useEffect(() => {
    if (!mutation.data && !mutation.error) return;
    const timer = setTimeout(() => mutation.reset(), 10_000);
    return () => clearTimeout(timer);
  }, [mutation.data, mutation.error]); // eslint-disable-line react-hooks/exhaustive-deps

  const cooldownMinutes = mutation.error?.remaining_minutes ?? 0;

  return {
    sync: mutation.mutate,
    isSyncing: mutation.isPending,
    result: mutation.data,
    error: mutation.error,
    cooldownMinutes,
    reset: mutation.reset,
  };
}
