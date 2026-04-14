"use client";

import { useState, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, Mail, RefreshCw } from "lucide-react";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { useHashScroll } from "../../../../hooks/useHashScroll";
import { useConnectionHealth } from "../../../../hooks/useConnectionHealth";
import { useSyncChannel } from "../../../../hooks/useSyncChannel";
import type { MetaAdsPeriod, MailDashboardTab } from "../../../../types/metrics";
import { ConnectionHealthBanner } from "../../../connection-health-banner";
import { PeriodSelector } from "../shared/PeriodSelector";
import { MailPanoramaTab } from "./tabs/MailPanoramaTab";
import { MailCampanasTab } from "./tabs/MailCampanasTab";
import { MailAutomatizacionesTab } from "./tabs/MailAutomatizacionesTab";

import { MailAudienciaTab } from "./tabs/MailAudienciaTab";
import { MailEntregabilidadV2Tab } from "./tabs/MailEntregabilidadV2Tab";
import { MailCrecimientoTab } from "./tabs/MailCrecimientoTab";

interface MailDashboardProps {
  onClose?: () => void;
  initialTab?: string;
  isRouteBased?: boolean;
}

const VALID_TABS: MailDashboardTab[] = [
  "panorama",
  "campanas",
  "automatizaciones",
  "audiencia",
  "entregabilidad",
  "crecimiento",
];

export function MailDashboard({ onClose, initialTab, isRouteBased }: MailDashboardProps) {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const tenantId = params?.tenantId as string;

  const tabFromUrl = searchParams?.get("tab") ?? initialTab ?? "panorama";
  const periodFromUrl = (searchParams?.get("period") ?? "30d") as MetaAdsPeriod;

  const [activeTab, setActiveTab] = useState<MailDashboardTab>(
    VALID_TABS.includes(tabFromUrl as MailDashboardTab)
      ? (tabFromUrl as MailDashboardTab)
      : "panorama",
  );
  const [period, setPeriod] = useState<MetaAdsPeriod>(periodFromUrl);

  const { data: health } = useConnectionHealth("email-nurture");
  const { sync, isSyncing, cooldownMinutes, result, error } = useSyncChannel("email-nurture");
  useHashScroll();

  useEffect(() => {
    if (result) toast.success("Sincronización completada");
  }, [result]);

  useEffect(() => {
    if (error) toast.error(error.detail ?? "Error al sincronizar");
  }, [error]);

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
    const tab = value as MailDashboardTab;
    setActiveTab(tab);
    const url = new URL(window.location.href);
    if (tab === "panorama") {
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
    router.push(`/${tenantId}/growth-studio/nutricion-oportunidad?channel=email-nurture`);
  }, [onClose, router, tenantId]);

  const dashboardContent = (
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
            <Mail className="h-5 w-5 text-amber-500" />
            <h1 className="text-lg font-semibold">Email Marketing &middot; Dashboard</h1>
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
            {isSyncing ? "Sincronizando..." : "Sincronizar"}
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
            <TabsTrigger value="panorama">Panorama</TabsTrigger>
            <TabsTrigger value="campanas">Campañas</TabsTrigger>
            <TabsTrigger value="automatizaciones">Automatizaciones</TabsTrigger>
            <TabsTrigger value="audiencia">Audiencia</TabsTrigger>
            <TabsTrigger value="entregabilidad">Entregabilidad</TabsTrigger>
            <TabsTrigger value="crecimiento">Crecimiento</TabsTrigger>
          </TabsList>
        </div>

        <div className="flex-1 overflow-y-auto">
          <TabsContent value="panorama" className="m-0 p-6">
            <MailPanoramaTab period={period} />
          </TabsContent>
          <TabsContent value="campanas" className="m-0 p-6">
            <MailCampanasTab period={period} />
          </TabsContent>
          <TabsContent value="automatizaciones" className="m-0 p-6">
            <MailAutomatizacionesTab period={period} />
          </TabsContent>
          <TabsContent value="audiencia" className="m-0 p-6">
            <MailAudienciaTab period={period} />
          </TabsContent>
          <TabsContent value="entregabilidad" className="m-0 p-6">
            <MailEntregabilidadV2Tab period={period} />
          </TabsContent>
          <TabsContent value="crecimiento" className="m-0 p-6">
            <MailCrecimientoTab period={period} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );

  if (isRouteBased) return dashboardContent;
  if (typeof document === "undefined") return null;
  return createPortal(dashboardContent, document.body);
}
