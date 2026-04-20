"use client";

import { ArrowLeft, AlertTriangle } from "lucide-react";
import { useRouter, useParams, useSearchParams } from "next/navigation";
import { useMemo, useState, useCallback } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

import { useCampaignPerformance } from "../../../../../api/campaigns-api";
import {
  useAssociations,
  useAutoDetectSuggestions,
  useOffersForAssignment,
  useMetaHealthCheck,
} from "../../../../../api/offer-association-api";
import { MetaAdsPeriodSelector } from "../MetaAdsPeriodSelector";

import { PendienteDetailPanel } from "./PendienteDetailPanel";
import { PendientesList } from "./PendientesList";

import type { PendingCampaign } from "./PendientesList";
import type { MetaAdsPeriod } from "../../../../../types/metrics";

interface PendientesViewProps {
  period?: MetaAdsPeriod;
  onPeriodChange?: (p: MetaAdsPeriod) => void;
  onBackToCampaigns?: () => void;
}

/**
 *
 */
export function PendientesView({
  period = "30d",
  onPeriodChange,
  onBackToCampaigns,
}: PendientesViewProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;
  const { currency: tenantCurrency } = useTenantLocale();

  const campaignFromUrl = searchParams?.get("campaign") ?? null;
  const [selectedId, setSelectedId] = useState<string | null>(campaignFromUrl);

  const { data: campaignData, isLoading: campaignsLoading } = useCampaignPerformance(period);
  const { data: associations, isLoading: assocLoading } = useAssociations();
  const { data: offers } = useOffersForAssignment();
  const { data: healthCheck } = useMetaHealthCheck();
  const autoDetect = useAutoDetectSuggestions();

  const isLoading = campaignsLoading || assocLoading;

  const associatedIds = useMemo(() => {
    const set = new Set<string>();
    for (const a of associations ?? []) {
      if (a.targetType === "campaign") {
        set.add(a.targetExternalId);
      }
    }
    return set;
  }, [associations]);

  const utmIssueIds = useMemo(() => {
    const set = new Set<string>();
    if (healthCheck?.activeCampaigns) {
      for (const c of healthCheck.activeCampaigns) {
        if (c.hasIssue && c.issueText?.toLowerCase().includes("utm")) {
          set.add(c.externalId);
        }
      }
    }
    return set;
  }, [healthCheck]);

  const pendingItems = useMemo<PendingCampaign[]>(() => {
    const campaigns = campaignData?.campaigns ?? [];
    const items: PendingCampaign[] = [];

    for (const c of campaigns) {
      if (!associatedIds.has(c.externalId)) {
        items.push({ campaign: c, reason: "no_offer" });
      } else if (utmIssueIds.has(c.externalId)) {
        items.push({ campaign: c, reason: "no_utm" });
      }
    }

    items.sort((a, b) => {
      const aActive = (a.campaign.effectiveStatus ?? "").toUpperCase() === "ACTIVE";
      const bActive = (b.campaign.effectiveStatus ?? "").toUpperCase() === "ACTIVE";
      if (aActive && !bActive) return -1;
      if (!aActive && bActive) return 1;
      return a.campaign.name.localeCompare(b.campaign.name);
    });

    return items;
  }, [campaignData?.campaigns, associatedIds, utmIssueIds]);

  const effectiveSelectedId =
    selectedId && pendingItems.some((i) => i.campaign.externalId === selectedId)
      ? selectedId
      : (pendingItems[0]?.campaign.externalId ?? null);

  const selectedCampaign = useMemo(
    () => pendingItems.find((i) => i.campaign.externalId === effectiveSelectedId)?.campaign ?? null,
    [pendingItems, effectiveSelectedId],
  );

  const currency = campaignData?.currency ?? tenantCurrency;

  const handleAssigned = useCallback(() => {
    const currentIndex = pendingItems.findIndex(
      (i) => i.campaign.externalId === effectiveSelectedId,
    );
    const nextItem = pendingItems[currentIndex + 1] ?? pendingItems[currentIndex - 1];
    setSelectedId(nextItem?.campaign.externalId ?? null);
  }, [pendingItems, effectiveSelectedId]);

  const handleBack = useCallback(() => {
    if (onBackToCampaigns) {
      onBackToCampaigns();
    } else {
      router.push(`/${tenantId}/growth-studio/atraccion-captura/meta-ads?tab=campanas`);
    }
  }, [onBackToCampaigns, router, tenantId]);

  if (!isLoading && !campaignData) {
    return (
      <Card className="m-6">
        <CardContent className="py-8 text-center">
          <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm font-medium">Error al cargar pendientes</p>
          <p className="text-xs text-muted-foreground mt-1">
            Intenta de nuevo o vuelve a la vista de campañas.
          </p>
          <Button variant="outline" size="sm" onClick={handleBack} className="mt-4 text-xs">
            Volver a Campañas
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-1.5 text-xs">
            <ArrowLeft className="h-3.5 w-3.5" />
            Campañas
          </Button>
          <h1 className="text-sm font-semibold flex items-center gap-2">
            Pendientes
            {pendingItems.length > 0 && (
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/15 text-amber-400 text-[10px] font-bold">
                {pendingItems.length}
              </span>
            )}
          </h1>
        </div>
        {onPeriodChange && <MetaAdsPeriodSelector value={period} onChange={onPeriodChange} />}
      </div>

      {/* Split view */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        <div className="w-full lg:w-[380px] lg:border-r border-zinc-800 overflow-hidden flex flex-col shrink-0">
          <PendientesList
            items={pendingItems}
            currency={currency}
            selectedId={effectiveSelectedId}
            onSelect={setSelectedId}
            isLoading={isLoading}
            onAutoDetect={() => void autoDetect.mutateAsync()}
            isAutoDetecting={autoDetect.isPending}
            onBackToCampaigns={handleBack}
          />
        </div>

        <div className="hidden lg:flex flex-1 overflow-hidden">
          <PendienteDetailPanel
            campaign={selectedCampaign}
            currency={currency}
            offers={offers ?? []}
            onAssigned={handleAssigned}
          />
        </div>
      </div>
    </div>
  );
}
