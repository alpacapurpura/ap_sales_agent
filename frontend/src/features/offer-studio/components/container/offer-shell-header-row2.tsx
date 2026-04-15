"use client";

import { useMemo } from "react";

import { FocusModeButton } from "@/features/copilot/components/focus-mode-button";
import { cn } from "@/lib/utils";

import { getSectionsForOffer, SECTION_REGISTRY } from "../../config/offer-builder-config";
import { getOfferHealth } from "../../utils/offer-health";

import { LandingActionButton } from "./landing-action-button";
import { OfferProgressBar } from "./offer-progress-bar";
import { useOfferShell } from "./offer-shell";

/**
 * Row 2 of the persistent shell — progress bar on the left, Landing action
 * button and "Autocompletar IA" on the right.
 */
export function OfferShellHeaderRow2() {
  const { offer, tenantId } = useOfferShell();

  const progress = useMemo(() => computeProgress(offer), [offer]);

  return (
    <div
      className={cn("flex h-[44px] items-center justify-between gap-4 border-b", "bg-card/30 px-6")}
    >
      <OfferProgressBar
        percentage={progress.percentage}
        completed={progress.completed}
        total={progress.total}
        nextMilestone={progress.nextMilestone}
        className="max-w-xl"
      />

      <div className="flex shrink-0 items-center gap-2">
        <LandingActionButton offerId={offer.id} tenantId={tenantId} />
        <FocusModeButton
          domain="offer"
          entityId={offer.id}
          label={offer.public_name ?? "Oferta"}
          entityData={offer as unknown as Record<string, unknown>}
        />
      </div>
    </div>
  );
}

interface ProgressSummary {
  percentage: number;
  completed: number;
  total: number;
  nextMilestone: string | null;
}

function computeProgress(offer: Parameters<typeof getOfferHealth>[0]): ProgressSummary {
  const health = getOfferHealth(offer);
  const sectionIds = getSectionsForOffer(offer);

  let completed = 0;
  let total = 0;
  let nextMilestoneId: string | null = null;

  for (const id of sectionIds) {
    const status = health.sections[id]?.status;
    if (status === "optional" || !status) continue;
    total += 1;
    if (status === "complete") {
      completed += 1;
    } else if (!nextMilestoneId) {
      nextMilestoneId = id;
    }
  }

  const nextMilestone = nextMilestoneId ? (SECTION_REGISTRY[nextMilestoneId]?.title ?? null) : null;

  return {
    percentage: health.completionPercentage,
    completed,
    total,
    nextMilestone,
  };
}
