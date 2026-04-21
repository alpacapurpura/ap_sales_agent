"use client";

import { Archive, ChevronLeft, Copy, History, MoreVertical } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

import { useChangeOfferStatus } from "../hooks/use-status-mutation";

import { OfferAutoSaveIndicator } from "./OfferAutoSaveIndicator";
import { OfferStatusChangeModal } from "./OfferStatusChangeModal";
import { OfferStatusSwitcher } from "./OfferStatusSwitcher";

import type { Offer } from "../types";
import type { OfferLifecycleStatus } from "../types/enums";

export interface OfferShellHeaderProps {
  offer: Offer;
  tenantId: string;
}

/**
 *
 */
export function OfferShellHeader({ offer, tenantId }: OfferShellHeaderProps) {
  const [pendingStatus, setPendingStatus] = useState<OfferLifecycleStatus | null>(null);

  const statusMutation = useChangeOfferStatus(offer.id, {
    onSuccess: () => setPendingStatus(null),
  });

  const currentStatus = offer.status as OfferLifecycleStatus;
  const formatLabel = buildFormatLabel(offer);

  const handleArchive = () => setPendingStatus("archived");
  const handleConfirm = () => {
    if (!pendingStatus) return;
    statusMutation.mutate({ status: pendingStatus });
  };

  return (
    <>
      <div
        className={cn(
          "flex h-[60px] items-center justify-between gap-4 border-b",
          "bg-background/80 px-6 backdrop-blur-sm",
        )}
      >
        <div className="flex min-w-0 items-center gap-3">
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0"
            aria-label="Volver al Offer Studio"
          >
            <Link href={`/${tenantId}/offer-studio`}>
              <ChevronLeft className="h-4 w-4" aria-hidden />
            </Link>
          </Button>

          <div className="flex min-w-0 flex-col">
            <div className="flex items-center gap-2">
              <h1 className="max-w-[320px] truncate text-lg font-bold text-foreground">
                {offer.name}
              </h1>
              {formatLabel ? (
                <Badge
                  variant="secondary"
                  className="text-[10px] font-semibold uppercase tracking-wider"
                >
                  {formatLabel}
                </Badge>
              ) : null}
            </div>
            <OfferAutoSaveIndicator state="idle" lastSavedAt={null} />
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <OfferStatusSwitcher
            currentStatus={currentStatus}
            onTransitionRequested={(target) => setPendingStatus(target)}
            disabled={statusMutation.isPending}
          />

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                aria-label="Más opciones de la oferta"
              >
                <MoreVertical className="h-4 w-4" aria-hidden />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem
                onSelect={(event) => {
                  event.preventDefault();
                  handleArchive();
                }}
                disabled={currentStatus === "archived" || statusMutation.isPending}
              >
                <Archive className="mr-2 h-4 w-4" aria-hidden />
                Archivar
              </DropdownMenuItem>
              <DropdownMenuItem disabled>
                <Copy className="mr-2 h-4 w-4" aria-hidden />
                Duplicar
                <span className="ml-auto text-[10px] uppercase text-muted-foreground">
                  Próximamente
                </span>
              </DropdownMenuItem>
              <DropdownMenuItem disabled>
                <History className="mr-2 h-4 w-4" aria-hidden />
                Historial
                <span className="ml-auto text-[10px] uppercase text-muted-foreground">
                  Próximamente
                </span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {pendingStatus ? (
        <OfferStatusChangeModal
          open
          fromStatus={currentStatus}
          toStatus={pendingStatus}
          offerName={offer.name}
          isSubmitting={statusMutation.isPending}
          onConfirm={handleConfirm}
          onCancel={() => {
            if (statusMutation.isPending) return;
            setPendingStatus(null);
          }}
        />
      ) : null}
    </>
  );
}

function buildFormatLabel(offer: { archetype?: string; format_hint?: string }): string | null {
  if (offer.archetype && offer.format_hint) {
    return `${offer.archetype} · ${offer.format_hint}`;
  }
  return offer.archetype ?? offer.format_hint ?? null;
}
