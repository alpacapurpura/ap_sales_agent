"use client";

import { useState, useCallback } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, Instagram, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams, useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { useChannelDashboard } from "../../../../hooks/useChannelDashboard";
import { useHashScroll } from "../../../../hooks/useHashScroll";
import { useSyncChannel } from "../../../../hooks/useSyncChannel";
import type { MetaAdsPeriod, IgOrganicDashboardTab } from "../../../../types/metrics";
import { ChannelPeriodSelector } from "./ChannelPeriodSelector";
import { IgOverviewTab } from "./tabs/IgOverviewTab";
import { IgContentTab } from "./tabs/IgContentTab";
import { IgAudienceTab } from "./tabs/IgAudienceTab";
import { IgReachTab } from "./tabs/IgReachTab";

interface IgOrganicDashboardProps {
  onClose?: () => void;
  initialTab?: string;
  isRouteBased?: boolean;
}

const VALID_TABS: IgOrganicDashboardTab[] = ["overview", "contenido", "audiencia", "alcance"];

export function IgOrganicDashboard({ onClose, initialTab, isRouteBased }: IgOrganicDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get("tab") ?? initialTab ?? "overview";
  const [activeTab, setActiveTab] = useState<IgOrganicDashboardTab>(
    VALID_TABS.includes(tabFromUrl as IgOrganicDashboardTab)
      ? (tabFromUrl as IgOrganicDashboardTab)
      : "overview",
  );
  const periodFromUrl = (searchParams?.get("period") ?? "30d") as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const { data, isLoading } = useChannelDashboard("ig-organic", period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel("ig-organic");
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
    const tab = value as IgOrganicDashboardTab;
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
    router.push(`/${tenantId}/growth-studio/atraccion-captura?channel=ig-organic`);
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
            <Instagram className="h-5 w-5 text-pink-500" />
            <h1 className="text-lg font-semibold">Instagram Orgánico &middot; Dashboard</h1>
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
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="contenido">Contenido</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="alcance">Alcance</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="overview" className="m-0 p-6">
            <IgOverviewTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="contenido" className="m-0 p-6">
            <IgContentTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <IgAudienceTab data={data} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="alcance" className="m-0 p-6">
            <IgReachTab data={data} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;
  if (typeof document === "undefined") return null;
  return createPortal(dashboardContent, document.body);
}
