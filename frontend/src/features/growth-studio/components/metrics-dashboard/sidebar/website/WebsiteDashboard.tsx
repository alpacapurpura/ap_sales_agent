"use client";

import { ArrowLeft, Globe, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import { useState, useCallback } from "react";
import { createPortal } from "react-dom";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

import { useChannelDashboard } from "../../../../hooks/use-channel-dashboard";
import { useHashScroll } from "../../../../hooks/use-hash-scroll";
import { useSyncChannel } from "../../../../hooks/use-sync-channel";
import { PeriodSelector } from "../shared/PeriodSelector";

import { WebsiteContentTab } from "./tabs/WebsiteContentTab";
import { WebsiteConversionsTab } from "./tabs/WebsiteConversionsTab";
import { WebsiteOverviewTab } from "./tabs/WebsiteOverviewTab";
import { WebsiteTrafficTab } from "./tabs/WebsiteTrafficTab";

import type { WebsiteDashboardTab, WebsiteData } from "./types";
import type { MetaAdsPeriod } from "../../../../types/metrics";

interface WebsiteDashboardProps {
  onClose?: () => void;
  initialTab?: string;
  isRouteBased?: boolean;
}

const VALID_TABS: WebsiteDashboardTab[] = ["overview", "trafico", "contenido", "conversiones"];

/**
 *
 */
export function WebsiteDashboard({ onClose, initialTab, isRouteBased }: WebsiteDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get("tab") ?? initialTab ?? "overview";
  const [activeTab, setActiveTab] = useState<WebsiteDashboardTab>(
    VALID_TABS.includes(tabFromUrl as WebsiteDashboardTab)
      ? (tabFromUrl as WebsiteDashboardTab)
      : "overview",
  );
  const periodFromUrl = (searchParams?.get("period") ?? "30d") as MetaAdsPeriod;
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);
  const { data, isLoading } = useChannelDashboard("website-total", period);
  const { sync, isSyncing, cooldownMinutes } = useSyncChannel("website-total");
  useHashScroll();

  const websiteData = data as WebsiteData | undefined;

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
    const tab = value as WebsiteDashboardTab;
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
    router.push(`/${tenantId}/growth-studio/atraccion-captura?channel=website-total`);
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
            <Globe className="h-5 w-5 text-blue-500" />
            <h1 className="text-lg font-semibold">Tu Sitio Web &middot; Dashboard</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <PeriodSelector value={period} onChange={handlePeriodChange} />
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
            <TabsTrigger value="trafico">Tráfico</TabsTrigger>
            <TabsTrigger value="contenido">Contenido</TabsTrigger>
            <TabsTrigger value="conversiones">Conversiones</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="overview" className="m-0 p-6">
            <WebsiteOverviewTab data={websiteData} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="trafico" className="m-0 p-6">
            <WebsiteTrafficTab data={websiteData} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="contenido" className="m-0 p-6">
            <WebsiteContentTab data={websiteData} isLoading={isLoading} />
          </TabsContent>
          <TabsContent value="conversiones" className="m-0 p-6">
            <WebsiteConversionsTab data={websiteData} isLoading={isLoading} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;
  if (typeof document === "undefined") return null;
  return createPortal(dashboardContent, document.body);
}
