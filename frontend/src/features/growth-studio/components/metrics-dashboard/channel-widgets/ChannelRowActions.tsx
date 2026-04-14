"use client";

import React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface ChannelRowActionsProps {
  /** Whether the channel has stale data (controls visibility of refresh button) */
  stale: boolean;
  /** Whether a refresh is currently in progress */
  refreshing: boolean;
  /** Whether the refresh is on cooldown (rate-limited) */
  cooldown: boolean;
  /** Callback to trigger a data refresh */
  onRefresh: () => void;
}

export const ChannelRowActions = React.memo(function ChannelRowActions({
  stale,
  refreshing,
  cooldown,
  onRefresh,
}: ChannelRowActionsProps) {
  if (!stale) return null;

  return (
    <Button
      variant="ghost"
      size="icon"
      className="h-7 w-7"
      onClick={onRefresh}
      disabled={refreshing || cooldown}
      title={cooldown ? "Disponible en unos minutos" : "Actualizar datos"}
    >
      <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
    </Button>
  );
});
