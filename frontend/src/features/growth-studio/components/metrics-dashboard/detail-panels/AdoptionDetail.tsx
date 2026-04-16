"use client";

import { Activity, Calendar, Clock, CornerDownLeft, Layers, Settings } from "lucide-react";
import React, { useState } from "react";

import { Button } from "@/components/ui/button";
import { useTenantLocale } from "@/features/tenant/context/tenant-locale-context";

import { useAdoptionDetail } from "../../../hooks/use-stage-detail";
import { ActionPanel } from "../action-widgets/ActionPanel";
import { MiniFunnel } from "../channel-widgets/MiniFunnel";
import { HealthBar } from "../offer-widgets/HealthBar";
import { OfferHealthCard } from "../offer-widgets/OfferHealthCard";
import { DetailEmpty } from "../ui/DetailEmpty";
import { DetailError } from "../ui/DetailError";
import { DetailSkeleton } from "../ui/DetailSkeleton";
import { formatLastUpdated, formatDualCurrency } from "../utils/format";

import { BottleneckBanner } from "./BottleneckBanner";

import type { MetricClickData, StageSummary } from "../../../types/metrics";

const ADOPCION_STAGE: StageSummary = {
  id: "ADOPCION",
  order: 5,
  label: "Adopción",
  description: "Salud y activación de clientes existentes",
  mainKpi: { label: "salud %", value: 0, unit: "%" },
  secondaryKpi: { label: "activos", value: 0 },
  hasDetail: true,
};

interface AdoptionDetailProps {
  onMetricClick?: (metric: MetricClickData) => void;
}

export const AdoptionDetail = React.memo(function AdoptionDetail({
  onMetricClick,
}: AdoptionDetailProps) {
  const { timezone } = useTenantLocale();
  const { data, isLoading, error, refetch } = useAdoptionDetail();
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  if (isLoading) {
    return (
      <DetailSkeleton isLoading>
        <></>
      </DetailSkeleton>
    );
  }

  if (error) {
    return (
      <DetailError
        error={error instanceof Error ? error : new Error("Error desconocido")}
        onRetry={() => {
          void refetch();
        }}
        lastData={data}
      />
    );
  }

  if (!data) {
    return <DetailEmpty stage={ADOPCION_STAGE} />;
  }

  // Empty state
  if (data.offers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <h3 className="text-sm font-semibold">Sin clientes registrados</h3>
        <p className="text-xs text-muted-foreground mt-2 max-w-md">
          Cuando completes tus primeras ventas, aqui veras como tus clientes usan tu producto o
          servicio.
        </p>
        <span className="text-xs text-primary underline mt-3 cursor-pointer">Ir a Ventas</span>
      </div>
    );
  }

  const { headerKpis, miniFunnel, offers, bottlenecks } = data;

  return (
    <div className="space-y-12 animate-fade-in bg-background p-6 rounded-2xl text-foreground border border-border">
      {/* Title & Actions Row */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground flex items-center gap-2">
            Adopción
            <span className="px-2 py-0.5 mt-1 rounded-full bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-medium tracking-wide">
              ETAPA 5
            </span>
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Salud y activación de clientes existentes post-venta.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <p className="text-xs text-muted-foreground italic mr-2">
            Actualizado: {data.lastUpdated ? formatLastUpdated(data.lastUpdated, timezone) : "Hoy"}
          </p>
          <Button variant="outline" onClick={() => setIsPanelOpen(true)}>
            <Calendar className="mr-2 h-4 w-4" /> Últimos 30 días
          </Button>
          <Button
            className="bg-emerald-600 hover:bg-emerald-700 text-white"
            onClick={() => setIsPanelOpen(true)}
          >
            <Settings className="mr-2 h-4 w-4" /> Gestionar Etapa
          </Button>
        </div>
      </div>

      <ActionPanel isOpen={isPanelOpen} onClose={() => setIsPanelOpen(false)} />

      {/* Global Performance Header */}
      <div className="bg-card rounded-xl p-6 shadow-sm border border-border relative overflow-hidden">
        <h2 className="text-lg font-semibold mb-6 flex items-center text-foreground/90">
          <Activity className="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-500" /> Estado de la
          Base de Clientes
        </h2>

        <div className="relative mb-2">
          {/* Horizontal Lines (Background Layer) */}
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-200 to-emerald-400 dark:from-emerald-900 dark:to-emerald-700 top-[40%] left-[20%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-400 to-emerald-500 dark:from-emerald-700 dark:to-emerald-500 top-[40%] left-[45%] z-0"></div>
          <div className="hidden md:block absolute w-[10%] h-[2px] bg-gradient-to-r from-emerald-500 to-emerald-600 dark:from-emerald-500 dark:to-emerald-400 top-[40%] left-[70%] z-0"></div>

          {/* Metrics Row (Foreground Layer) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10 w-full">
            {/* Bloque 1: Ventas (Input) */}
            <div className="bg-muted/30 p-5 rounded-lg border border-border shadow-sm flex flex-col items-center justify-center relative text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase mb-1">
                Ventas Generadas
              </span>
              <span className="text-3xl font-black text-foreground">
                {miniFunnel.sourceValue.toLocaleString("es-ES")}
              </span>
              <span className="text-xs text-muted-foreground mt-1">Clientes Nuevos</span>
            </div>

            {/* Bloque 2: Clientes Activos */}
            <div className="bg-background p-5 rounded-lg border border-emerald-500/20 shadow-sm flex flex-col items-center justify-center relative text-center ring-1 ring-emerald-500/10">
              <span className="text-[10px] text-emerald-600 dark:text-emerald-500 font-bold uppercase mb-1">
                Clientes Activos
              </span>
              <span className="text-4xl font-black text-emerald-600 dark:text-emerald-500">
                {headerKpis.activeCustomers.toLocaleString("es-ES")}
              </span>
              <span className="text-xs text-emerald-600/80 dark:text-emerald-500/80 mt-1 font-medium">
                Consumiendo el producto
              </span>
              <div className="mt-3 text-[10px] text-muted-foreground font-medium flex items-center justify-center">
                <Clock className="w-3 h-3 mr-1 text-emerald-600 dark:text-emerald-500" />
                <span>
                  Activación Promedio:{" "}
                  {headerKpis.avgTtvDays != null
                    ? `${Math.round(headerKpis.avgTtvDays)} días`
                    : "--"}
                </span>
              </div>
            </div>

            {/* Bloque 3: Tasa de Salud */}
            <div className="flex flex-col items-center justify-center relative">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-500 dark:from-emerald-600 dark:to-emerald-500 text-white flex items-center justify-center shadow-md border-4 border-background">
                <span className="font-bold text-lg">{headerKpis.healthPct.toFixed(1)}%</span>
              </div>
              <span className="text-[10px] text-muted-foreground font-bold uppercase mt-3 text-center">
                Tasa de Salud
              </span>
            </div>

            {/* Bloque 4: Clientes Inactivos */}
            <div className="bg-background p-5 rounded-lg border border-border shadow-sm flex flex-col items-center justify-center relative text-center">
              <span className="text-[10px] text-muted-foreground font-bold uppercase mb-1">
                Clientes Inactivos
              </span>
              <span className="text-4xl font-black text-muted-foreground">
                {headerKpis.inactiveCustomers.toLocaleString("es-ES")}
              </span>
              <span className="text-xs text-muted-foreground mt-1">Requieren atención</span>
              <div className="mt-3 text-[10px] text-muted-foreground font-medium flex items-center justify-center">
                <CornerDownLeft className="w-3 h-3 mr-1 text-muted-foreground" />
                <span>Devoluciones: {headerKpis.refundCount}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Health Bar Wrapper */}
      <div className="bg-card p-6 rounded-xl border border-border shadow-sm mb-8">
        <div className="flex justify-between items-end mb-4">
          <div>
            <h3 className="font-semibold text-foreground text-sm">Distribución de Salud General</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Proporción de clientes activos vs inactivos en toda tu cartera.
            </p>
          </div>
          <div className="text-right">
            <span
              className={`text-xs font-bold px-2 py-1 rounded-full ${headerKpis.healthPct >= 80 ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400" : headerKpis.healthPct >= 50 ? "bg-amber-50 text-amber-600 dark:bg-amber-950/30 dark:text-amber-400" : "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"}`}
            >
              {headerKpis.healthPct >= 80
                ? "Excelente"
                : headerKpis.healthPct >= 50
                  ? "Regular"
                  : "En Riesgo"}
            </span>
          </div>
        </div>
        <HealthBar
          activeCount={headerKpis.activeCustomers}
          inactiveCount={headerKpis.inactiveCustomers}
        />
        <div className="flex justify-between mt-3 text-xs font-medium">
          <span className="text-emerald-600 dark:text-emerald-500 flex items-center">
            <span className="w-2 h-2 rounded-full bg-emerald-500 mr-1.5"></span>
            {headerKpis.activeCustomers} Activos ({headerKpis.healthPct.toFixed(0)}%)
          </span>
          <span className="text-amber-600 dark:text-amber-500 flex items-center">
            <span className="w-2 h-2 rounded-full bg-amber-400 mr-1.5"></span>
            {headerKpis.inactiveCustomers} Inactivos ({(100 - headerKpis.healthPct).toFixed(0)}%)
          </span>
        </div>
      </div>

      {/* Bottleneck Banners */}
      {bottlenecks.length > 0 && (
        <div className="space-y-2">
          {bottlenecks.map((b) => (
            <BottleneckBanner
              key={`${b.type}-${b.metricLabel}`}
              bottleneck={{
                type: b.type as "abandoned_cart" | "meeting_no_show",
                metricLabel: b.metricLabel,
                currentRate: b.currentRate,
                severity: b.severity,
                threshold: b.threshold,
                tip: b.tip,
              }}
            />
          ))}
        </div>
      )}

      {/* DESGLOSE POR OFERTA */}
      <div className="space-y-4">
        <div className="flex items-end justify-between border-b border-border pb-2 mb-4">
          <div>
            <h3 className="font-semibold text-xl flex items-center text-foreground/90">
              <Layers className="w-5 h-5 mr-2 text-emerald-600 dark:text-emerald-500" /> Desglose de
              Adopción por Oferta
            </h3>
            <p className="text-sm text-muted-foreground mt-1">
              Métricas de salud y activación específicas para cada producto o servicio.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {offers.map((offer) => (
            <div
              key={offer.offerId}
              className={onMetricClick ? "cursor-pointer" : ""}
              onClick={
                onMetricClick
                  ? () =>
                      onMetricClick({
                        stageId: "ADOPCION",
                        channelSlug: offer.offerId,
                        metricName: "health_pct",
                        currentValue: offer.healthPct,
                      })
                  : undefined
              }
              role={onMetricClick ? "button" : undefined}
              tabIndex={onMetricClick ? 0 : undefined}
              onKeyDown={
                onMetricClick
                  ? (e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        onMetricClick({
                          stageId: "ADOPCION",
                          channelSlug: offer.offerId,
                          metricName: "health_pct",
                          currentValue: offer.healthPct,
                        });
                      }
                    }
                  : undefined
              }
            >
              <OfferHealthCard offer={offer} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});
