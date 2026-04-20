"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { syncChannel } from "../api/sync-channel-api";

import type { SyncChannelResult, SyncChannelError } from "../api/sync-channel-api";

/**
 *
 */
export function useSyncChannel(channelSlug: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const mutation = useMutation<SyncChannelResult, SyncChannelError>({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) throw { detail: "No auth token" } as SyncChannelError;
      return syncChannel(token, channelSlug);
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
  const mutationReset = mutation.reset;
  useEffect(() => {
    if (!mutation.data && !mutation.error) return;
    const timer = setTimeout(() => mutationReset(), 10_000);
    return () => clearTimeout(timer);
  }, [mutation.data, mutation.error, mutationReset]);

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
