"use client";

import * as React from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { useCampaignStatsQuery } from "../api/use-campaign-stats-query";

import type { CampaignStatsResponse } from "../types";

interface CampaignStatsCardProps {
  campaignId: string;
}

function StatItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-lg font-semibold">{value}</span>
    </div>
  );
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

function StatsContent({ stats }: { stats: CampaignStatsResponse }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <StatItem label="Total tareas" value={stats.total_tasks} />
      <StatItem label="Enviados" value={stats.sent_count} />
      <StatItem label="Respondidos" value={stats.responded_count} />
      <StatItem label="Convertidos" value={stats.converted_count} />
      <StatItem label="Tasa respuesta" value={formatPercent(stats.response_rate)} />
      <StatItem label="Tasa conversión" value={formatPercent(stats.conversion_rate)} />
    </div>
  );
}

/**
 * Tarjeta de estadísticas de una campaña.
 * Consume GET /api/v1/campaigns/{id}/stats.
 */
export function CampaignStatsCard({ campaignId }: CampaignStatsCardProps) {
  const { data, isLoading, isError, refetch } = useCampaignStatsQuery(campaignId);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Estadísticas</CardTitle>
        <CardDescription>Rendimiento de la campaña</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3" aria-busy="true">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex flex-col gap-1">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-6 w-12" />
              </div>
            ))}
          </div>
        )}
        {isError && !isLoading && (
          <div role="alert" className="flex flex-col gap-2 text-sm text-muted-foreground">
            <span>No se pudieron cargar las estadísticas.</span>
            <button
              type="button"
              onClick={() => void refetch()}
              className="text-primary hover:underline self-start text-xs"
            >
              Reintentar
            </button>
          </div>
        )}
        {!isLoading && !isError && data && <StatsContent stats={data} />}
        {!isLoading && !isError && !data && (
          <p className="text-sm text-muted-foreground">Aún no hay datos disponibles.</p>
        )}
      </CardContent>
    </Card>
  );
}
