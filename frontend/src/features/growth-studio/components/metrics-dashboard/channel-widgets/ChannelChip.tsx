"use client";

import { AlertTriangle } from "lucide-react";
import React from "react";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { getChannelIcon, getChannelColor } from "../../../lib/channelIcons";

import type { ChannelMetric } from "../../../types/metrics";

export interface ChannelChipProps {
  channel: ChannelMetric;
  variant: "disconnected" | "no-data";
  onDisconnectedClick?: (channel: ChannelMetric) => void;
  onNoDataClick?: (channel: ChannelMetric) => void;
}

const TOOLTIP_TEXT = {
  disconnected: "Desconectado, haga clic para conectar",
  "no-data": "Conectado pero sin datos, ¡revisemos cómo podemos usarlo!",
} as const;

export const ChannelChip = React.memo(function ChannelChip({
  channel,
  variant,
  onDisconnectedClick,
  onNoDataClick,
}: ChannelChipProps) {
  const iconColor = getChannelColor(channel.slug);
  const Icon = getChannelIcon(channel.slug);
  const tooltipText = TOOLTIP_TEXT[variant];

  const ariaLabel =
    variant === "disconnected"
      ? `${channel.name} — desconectado, clic para conectar`
      : `${channel.name} — sin datos`;

  const handleClick = () => {
    if (variant === "disconnected") {
      onDisconnectedClick?.(channel);
    } else {
      onNoDataClick?.(channel);
    }
  };

  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            aria-label={ariaLabel}
            onClick={handleClick}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all duration-150 cursor-pointer border",
              variant === "disconnected" &&
                "bg-muted/60 text-muted-foreground border-border/50 opacity-60 hover:opacity-90 hover:bg-muted",
              variant === "no-data" &&
                "bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/20 hover:bg-amber-100 dark:hover:bg-amber-500/20",
            )}
          >
            {/* eslint-disable-next-line react-hooks/static-components */}
            <Icon
              className="w-3.5 h-3.5 shrink-0"
              style={{ color: variant === "disconnected" ? undefined : iconColor }}
              aria-hidden="true"
            />
            <span className="truncate max-w-[120px]">{channel.name}</span>
            {variant === "no-data" && (
              <AlertTriangle
                data-testid="alert-icon"
                className="w-3 h-3 shrink-0"
                aria-hidden="true"
              />
            )}
          </button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltipText}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
});
