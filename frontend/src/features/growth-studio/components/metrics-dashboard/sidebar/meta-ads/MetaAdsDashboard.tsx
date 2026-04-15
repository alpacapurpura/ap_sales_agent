"use client";

import { ArrowLeft, BarChart3, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import { useState, useCallback, useMemo } from "react";
import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";
import { formatTenantDateTime } from "@/lib/format-date";
import { cn } from "@/lib/utils";

import { useCampaignPerformance } from "../../../../api/campaigns-api";
import { useAssociations, useMetaHealthCheck } from "../../../../api/offer-association-api";
import { useChannelDashboard } from "../../../../hooks/useChannelDashboard";
import { useConnectionHealth } from "../../../../hooks/useConnectionHealth";
import { useHashScroll } from "../../../../hooks/useHashScroll";
import { useSyncChannel } from "../../../../hooks/useSyncChannel";
import { ConnectionHealthBanner } from "../../../connection-health-banner";

import { computeMetaAdsOnboardingTrigger } from "./hooks/useMetaAdsOnboardingTrigger";
import { MetaAdsOnboardingModal } from "./MetaAdsOnboardingModal";
import { MetaAdsPeriodSelector } from "./MetaAdsPeriodSelector";
import { AudienciaTab } from "./tabs/AudienciaTab";
import { CampaignsTab } from "./tabs/CampaignsTab";
import { ResumenTab } from "./tabs/ResumenTab";

import type { MetaAdsPeriod, MetaAdsDashboardTab } from "../../../../types/metrics";

import { CreativosTab } from "./tabs/CreativosTab";
import { CostosTab } from "./tabs/CostosTab";
import { PendientesTab } from "./tabs/PendientesTab";
import { useMetaAdsNotices } from "./notices/useMetaAdsNotices";
import { TabBadge } from "./notices/TabBadge";

const ONBOARDING_DISMISSED_KEY = "meta-ads-onboarding-dismissed";

interface MetaAdsDashboardProps {
  onClose?: () => void;
  initialTab?: MetaAdsDashboardTab;
  isRouteBased?: boolean;
}

const VALID_TABS: MetaAdsDashboardTab[] = [
  "resumen",
  "campanas",
  "pendientes",
  "creativos",
  "audiencia",
  "costos",
];

// eslint-disable-next-line sonarjs/cognitive-complexity -- TODO: extract tab management and route logic to hooks
export function MetaAdsDashboard({ onClose, initialTab, isRouteBased }: MetaAdsDashboardProps) {
  const { timezone } = useTenantLocale();
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get("tab") ?? initialTab ?? "resumen";
  const periodFromUrl = (searchParams?.get("period") ?? "30d") as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const [activeTab, setActiveTab] = useState<MetaAdsDashboardTab>(
    VALID_TABS.includes(tabFromUrl as MetaAdsDashboardTab)
      ? (tabFromUrl as MetaAdsDashboardTab)
      : "resumen",
  );
  const { data: dashboardData, isLoading: isDashboardLoading } = useChannelDashboard(
    "meta-ads",
    period,
  );
  const { data: campaignData, isLoading: isCampaignLoading } = useCampaignPerformance(period);
  const { data: health } = useConnectionHealth("meta-ads");
  const { data: associations } = useAssociations();
  const { data: metaHealthCheck } = useMetaHealthCheck();
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel("meta-ads");
  useHashScroll();

  // Pending campaign count for the tab badge (cheap — no useMemo needed)
  let unassignedCount = 0;
  if (campaignData?.campaigns && associations) {
    const assocIds = new Set<string>();
    for (const a of associations) {
      if (a.targetType === "campaign") assocIds.add(a.targetExternalId);
    }
    for (const c of campaignData.campaigns) {
      if (!assocIds.has(c.externalId)) unassignedCount++;
    }
  }

  // Unified improvement notices (active campaigns only, deduped, ignorable
  // for 24h via localStorage). Computed once at the dashboard level so both
  // the tab badges and the Resumen overview see the same data.
  const noticesSummary = useMetaAdsNotices({
    campaignData,
    healthCheck: metaHealthCheck,
  });

  // Onboarding modal: first-connect trigger. Derived state — no useEffect needed.
  // Gating (isOpen) and the projected campaign list are both computed by a
  // pure helper so the trigger logic can be unit-tested in isolation and so
  // the modal does not flicker while `campaignData`/`associations` resolve at
  // different times. See `hooks/useMetaAdsOnboardingTrigger.ts`.
  const [hasUserDismissedOnboarding, setHasUserDismissedOnboarding] = useState(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem(ONBOARDING_DISMISSED_KEY) === "1";
    } catch {
      return false;
    }
  });

  const { isOpen: isOnboardingOpen, campaigns: onboardingCampaigns } = useMemo(
    () =>
      computeMetaAdsOnboardingTrigger({
        campaignData,
        associations,
        hasUserDismissed: hasUserDismissedOnboarding,
      }),
    [campaignData, associations, hasUserDismissedOnboarding],
  );

  const handleOnboardingOpenChange = useCallback((open: boolean) => {
    if (!open) {
      try {
        localStorage.setItem(ONBOARDING_DISMISSED_KEY, "1");
      } catch {
        /* noop */
      }
      setHasUserDismissedOnboarding(true);
    }
  }, []);

  const handleOpenAssignCampaigns = useCallback(() => {
    setActiveTab("campanas");
    const url = new URL(window.location.href);
    url.searchParams.set("tab", "campanas");
    url.searchParams.set("assign", "true");
    window.history.replaceState(null, "", url.toString());
  }, []);

  const handlePeriodChange = useCallback((p: MetaAdsPeriod) => {
    setPeriod(p);
    const url = new URL(window.location.href);
    if (p === "30d") {
      url.searchParams.delete("period");
    } else {
      url.searchParams.set("period", p);
    }
    window.history.replaceState(null, "", url.toString());
  }, []);

  const handleTabChange = useCallback((value: string) => {
    const tab = value as MetaAdsDashboardTab;
    setActiveTab(tab);
    const url = new URL(window.location.href);
    if (tab === "resumen") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", tab);
    }
    // Regular tab clicks should not force the notices panel open.
    url.searchParams.delete("notices");
    window.history.replaceState(null, "", url.toString());
  }, []);

  // Deep-link navigation from the Resumen overview: change tab + auto-open
  // that tab's ImprovementNotesPanel by writing `?notices=open` into the URL.
  // The target tab reads it via useSearchParams and resets it after mount.
  const handleNavigateFromOverview = useCallback((tab: MetaAdsDashboardTab) => {
    setActiveTab(tab);
    const url = new URL(window.location.href);
    if (tab === "resumen") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", tab);
    }
    url.searchParams.set("notices", "open");
    window.history.replaceState(null, "", url.toString());
  }, []);

  const handleBack = useCallback(() => {
    if (onClose) {
      onClose();
      return;
    }
    router.push(`/${tenantId}/growth-studio/atraccion-captura?channel=meta-ads`);
  }, [onClose, router, tenantId]);

  const content = (
    <div
      className={
        isRouteBased
          ? "flex flex-col min-h-screen bg-background"
          : "fixed inset-0 z-50 flex flex-col bg-background"
      }
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <h1 className="text-lg font-semibold">Meta Ads &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <MetaAdsPeriodSelector value={period} onChange={handlePeriodChange} />
          {campaignData?.lastSynced && (
            <span className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Última sync: {formatTenantDateTime(campaignData.lastSynced, timezone)}
            </span>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => sync()}
            disabled={isSyncing || cooldownMinutes > 0}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={cn("h-3 w-3", isSyncing && "animate-spin")} />
            {isSyncing ? "Sincronizando…" : "Sincronizar"}
          </Button>
        </div>
      </div>

      {/* Connection Health Banner */}
      {health && health.status !== "healthy" && (
        <div className="px-6 pt-4">
          <ConnectionHealthBanner
            status={health.status}
            channelSlug={health.channelSlug}
            message={health.message}
            expiresAt={health.expiresAt}
          />
        </div>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="resumen">Resumen</TabsTrigger>
            <TabsTrigger value="campanas">
              Campañas
              <TabBadge
                count={noticesSummary.perTabCounts.campanas}
                severity={noticesSummary.maxSeverityPerTab.campanas}
              />
            </TabsTrigger>
            <TabsTrigger value="pendientes">
              Pendientes
              {unassignedCount > 0 && (
                <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] rounded-full bg-amber-500/15 px-1 text-[10px] font-bold text-amber-400">
                  {unassignedCount}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="creativos">
              Creativos
              <TabBadge
                count={noticesSummary.perTabCounts.creativos}
                severity={noticesSummary.maxSeverityPerTab.creativos}
              />
            </TabsTrigger>
            <TabsTrigger value="audiencia">
              Audiencia
              <TabBadge
                count={noticesSummary.perTabCounts.audiencia}
                severity={noticesSummary.maxSeverityPerTab.audiencia}
              />
            </TabsTrigger>
            <TabsTrigger value="costos">
              Costos
              <TabBadge
                count={noticesSummary.perTabCounts.costos}
                severity={noticesSummary.maxSeverityPerTab.costos}
              />
            </TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="resumen" className="m-0 p-6">
            <ResumenTab
              data={dashboardData}
              isLoading={isDashboardLoading}
              campaignData={campaignData}
              period={period}
              onNavigateToTab={handleNavigateFromOverview}
              onAssignCampaigns={handleOpenAssignCampaigns}
              noticesSummary={noticesSummary}
            />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <CampaignsTab
              data={campaignData}
              isLoading={isCampaignLoading}
              currency={
                campaignData?.currency ?? dashboardData?.kpis.find((k) => k.currency)?.currency
              }
              period={period}
              notices={noticesSummary.byTab.campanas}
              noticesSeverity={noticesSummary.severityPerTab.campanas}
              onNavigateToPendientes={() => handleTabChange("pendientes")}
            />
          </TabsContent>
          <TabsContent value="pendientes" className="m-0 flex-1">
            <PendientesTab
              period={period}
              onPeriodChange={handlePeriodChange}
              onBackToCampaigns={() => handleTabChange("campanas")}
            />
          </TabsContent>
          <TabsContent value="creativos" className="m-0 p-6">
            <CreativosTab data={dashboardData} isLoading={isDashboardLoading} period={period} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <AudienciaTab data={dashboardData} isLoading={isDashboardLoading} period={period} />
          </TabsContent>
          <TabsContent value="costos" className="m-0 p-6">
            <CostosTab
              data={dashboardData}
              campaignData={campaignData}
              isLoading={isDashboardLoading}
            />
          </TabsContent>
        </div>
      </Tabs>

      {/* Onboarding modal (first-connect trigger) */}
      <MetaAdsOnboardingModal
        open={isOnboardingOpen}
        onOpenChange={handleOnboardingOpenChange}
        campaigns={onboardingCampaigns}
        onAssignNow={handleOpenAssignCampaigns}
      />
    </div>
  );

  if (isRouteBased) return content;
  if (typeof document === "undefined") return null;
  return createPortal(content, document.body);
}
