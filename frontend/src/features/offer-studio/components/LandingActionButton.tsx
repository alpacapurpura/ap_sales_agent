"use client";

import { CheckCircle2, ExternalLink, Loader2, Sparkles, Wand2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import { useLandingStatus } from "../hooks/use-landing-status";

import { GenerateLandingConfirmDialog } from "./GenerateLandingConfirmDialog";
import { LandingKebabMenu } from "./LandingKebabMenu";

export interface LandingActionButtonProps {
  offerId: string;
  tenantId: string;
}

/**
 * Four-state contextual button for the landing page:
 *
 * 1. `disabled`           — offer < 90 % complete. Button is disabled and
 *                          shows the completion deficit. Tooltip explains.
 * 2. `ready-to-generate`  — offer ≥ 90 % but no landing yet. Clicking opens
 *                          `GenerateLandingConfirmDialog` → fires mutation.
 * 3. `in-sync`            — landing exists and matches the current offer.
 *                          Clicking opens the public URL in a new tab.
 *                          A kebab menu exposes Regenerar / Editar / Despublicar.
 * 4. `outdated`           — landing exists but the offer changed since
 *                          generation. Same as `in-sync` but with a pulsing
 *                          amber accent and "Regenerar (recomendado)" at the
 *                          top of the kebab.
 */
export function LandingActionButton({ offerId, tenantId }: LandingActionButtonProps) {
  const {
    data: status,
    uiState,
    generate,
    regenerate,
    unpublish,
    isLoading,
  } = useLandingStatus(offerId);

  const [confirmOpen, setConfirmOpen] = useState(false);

  if (isLoading || !status || !uiState) {
    return (
      <Button
        variant="outline"
        size="sm"
        disabled
        className="h-8 gap-1.5"
        data-testid="landing-loading"
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
        Landing
      </Button>
    );
  }

  if (uiState === "disabled") {
    const deficit = Math.max(0, 90 - status.completion_percentage);
    return (
      <TooltipProvider delayDuration={200}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span>
              <Button variant="outline" size="sm" disabled className="h-8 gap-1.5 opacity-60">
                <Wand2 className="h-3.5 w-3.5" />
                Generar landing
                <span className="ml-1 rounded bg-muted/60 px-1 text-[10px] font-bold">
                  Faltan {deficit}%
                </span>
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent>
            Completá al menos 90% de la oferta para generar la landing con IA.
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  if (uiState === "ready-to-generate") {
    return (
      <>
        <Button
          size="sm"
          className="h-8 gap-1.5"
          onClick={() => setConfirmOpen(true)}
          disabled={generate.isPending}
        >
          {generate.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <Sparkles className="h-3.5 w-3.5" />
          )}
          Generar landing con IA
        </Button>
        <GenerateLandingConfirmDialog
          open={confirmOpen}
          isSubmitting={generate.isPending}
          onCancel={() => setConfirmOpen(false)}
          onConfirm={() => {
            generate.mutate(undefined, {
              onSettled: () => setConfirmOpen(false),
            });
          }}
        />
      </>
    );
  }

  // in-sync OR outdated — both have the "Abrir landing" button + kebab
  const isOutdated = uiState === "outdated";
  const landingUrl = status.landing_url;

  const openLanding = () => {
    if (!landingUrl) return;
    window.open(landingUrl, "_blank", "noopener,noreferrer");
  };

  const button = (
    <Button
      variant="outline"
      size="sm"
      onClick={openLanding}
      disabled={!landingUrl}
      className={cn(
        "h-8 gap-1.5",
        isOutdated && "border-warning/60 text-warning hover:text-warning",
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          isOutdated ? "animate-pulse bg-warning" : "bg-success",
        )}
        data-testid={isOutdated ? "landing-outdated-dot" : "landing-synced-dot"}
        aria-hidden
      />
      {isOutdated ? (
        <CheckCircle2 className="h-3.5 w-3.5 text-warning" />
      ) : (
        <CheckCircle2 className="h-3.5 w-3.5 text-success" />
      )}
      Abrir landing
      <ExternalLink className="h-3.5 w-3.5 opacity-70" />
    </Button>
  );

  return (
    <div className="flex items-center gap-1">
      {isOutdated ? (
        <TooltipProvider delayDuration={200}>
          <Tooltip>
            <TooltipTrigger asChild>{button}</TooltipTrigger>
            <TooltipContent>
              Tu oferta cambió desde que generaste la landing. Regenerá para sincronizarla.
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      ) : (
        button
      )}
      <LandingKebabMenu
        tenantId={tenantId}
        offerId={offerId}
        isOutdated={isOutdated}
        onRegenerate={() => regenerate.mutate()}
        onUnpublish={() => unpublish.mutate()}
      />
    </div>
  );
}
