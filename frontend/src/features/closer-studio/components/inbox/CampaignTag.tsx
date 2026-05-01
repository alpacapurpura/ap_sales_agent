"use client";

import Link from "next/link";

import { badgeVariants } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

/** Maximum characters to show in the badge label before truncating. */
const MAX_NAME_LENGTH = 30;

export interface CampaignTagProps {
  campaignId: string;
  campaignName: string;
  /**
   * "list" (default) → compact chip apto para filas de ConversationItem.
   * "detail" → etiqueta ligeramente más grande para el header de ConversationThread.
   */
  variant?: "list" | "detail";
  className?: string;
}

/**
 * Chip de campaña — Shadcn Badge clickable que lleva a /campanas/{campaignId}.
 *
 * Muestra el nombre de la campaña con el prefijo "campaña: " en español neutro.
 * Trunca nombres con más de 30 caracteres y muestra el nombre completo en tooltip.
 */
export function CampaignTag({
  campaignId,
  campaignName,
  variant = "list",
  className,
}: CampaignTagProps) {
  const isTruncated = campaignName.length > MAX_NAME_LENGTH;
  const displayName = isTruncated ? `${campaignName.slice(0, MAX_NAME_LENGTH)}…` : campaignName;

  const label = `campaña: ${displayName}`;

  const chip = (
    <span title={isTruncated ? campaignName : undefined} className={cn("inline-flex", className)}>
      <Link
        href={`/campanas/${campaignId}`}
        prefetch={false}
        className={cn(
          badgeVariants({ variant: "secondary" }),
          "cursor-pointer select-none transition-opacity hover:opacity-80",
          variant === "detail" ? "text-xs px-2 py-0.5" : "text-[10px] px-1.5 py-0.5",
        )}
      >
        {label}
      </Link>
    </span>
  );

  if (!isTruncated) {
    return chip;
  }

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>{chip}</TooltipTrigger>
        <TooltipContent>
          <p>campaña: {campaignName}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
