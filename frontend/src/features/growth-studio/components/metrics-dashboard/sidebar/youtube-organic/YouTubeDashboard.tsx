"use client";

import { ArrowLeft, Youtube, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import { useState, useCallback } from "react";
import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import { useChannelDashboard } from "../../../../hooks/useChannelDashboard";
import { useHashScroll } from "../../../../hooks/useHashScroll";
import { useSyncChannel } from "../../../../hooks/useSyncChannel";
import { ChannelPeriodSelector } from "../ig-organic/ChannelPeriodSelector";

import { YtAudienceTab } from "./tabs/YtAudienceTab";
import { YtEngagementTab } from "./tabs/YtEngagementTab";
import { YtOverviewTab } from "./tabs/YtOverviewTab";
import { YtRetentionTab } from "./tabs/YtRetentionTab";
import { YtVideosTab } from "./tabs/YtVideosTab";

import type { MetaAdsPeriod, YouTubeDashboardTab } from "../../../../types/metrics";

interface YouTubeDashboardProps {
  onClose?: () => void;
  initialTab?: string;
  isRouteBased?: boolean;
}

const VALID_TABS: YouTubeDashboardTab[] = [
  "overview",
  "videos",
  "audiencia",
  "engagement",
  "retencion",
];

export function YouTubeDashboard({ onClose, initialTab, isRouteBased }: YouTubeDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get("tab") ?? initialTab ?? "overview";
  const [activeTab, setActiveTab] = useState<YouTubeDashboardTab>(
    VALID_TABS.includes(tabFromUrl as YouTubeDashboardTab)
      ? (tabFromUrl as YouTubeDashboardTab)
      : "overview",
  );
  const periodFromUrl = (searchParams?.get("period") ?? "30d") as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const { data, isLoading } = useChannelDashboard("yt-organic", period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel("yt-organic");
  useHashScroll();

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
    const tab = value as YouTubeDashboardTab;
    setActiveTab(tab);
    const url = new URL(window.location.href);
    if (tab === "overview") {
      url.searchParams.delete("tab");
    } else {
      url.searchParams.set("tab", tab);
    }
    window.history.replaceState(null, "", url.toString());
  }, []);

  const handleBack = useCallback(() => {
    if (onClose) {
      onClose();
      return;
    }
    router.push(`/${tenantId}/growth-studio/atraccion-captura?channel=yt-organic`);
  }, [onClose, router, tenantId]);

  const dashboardContent = (
    <div
      className={
        isRouteBased
          ? "flex flex-col min-h-screen bg-background"
          : "fixed inset-0 z-50 flex flex-col bg-background"
      }
    >
      <div className="flex items-center justify-between border-b px-6 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={handleBack} className="gap-1.5">
            <ArrowLeft className="h-4 w-4" />
            Volver
          </Button>
          <div className="flex items-center gap-2">
            <Youtube className="h-5 w-5 text-red-500" />
            <h1 className="text-lg font-semibold">YouTube Org&aacute;nico &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ChannelPeriodSelector value={period} onChange={handlePeriodChange} />
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

      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="flex flex-1 flex-col overflow-hidden"
      >
        <div className="border-b px-6">
          <TabsList className="h-10">
            <TabsTrigger value="overview">Resumen</TabsTrigger>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="engagement">Engagement</TabsTrigger>
            <TabsTrigger value="retencion">Retenci&oacute;n</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="overview" className="m-0 p-6">
            <YtOverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="videos" className="m-0 p-6">
            <YtVideosTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <YtAudienceTab />
          </TabsContent>
          <TabsContent value="engagement" className="m-0 p-6">
            <YtEngagementTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="retencion" className="m-0 p-6">
            <YtRetentionTab data={data} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;

  if (typeof document === "undefined") return null;
  return createPortal(dashboardContent, document.body);
}
