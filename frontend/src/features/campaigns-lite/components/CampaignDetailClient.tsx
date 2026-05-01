"use client";

import * as React from "react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import { useCampaignDetailQuery } from "../api/use-campaign-detail-query";

import { CampaignLifecycleButtons } from "./CampaignLifecycleButtons";
import { CampaignStatsCard } from "./CampaignStatsCard";

import type { CampaignStatus } from "../types";

interface CampaignDetailClientProps {
  campaignId: string;
}

const STATUS_LABELS: Record<CampaignStatus, string> = {
  DRAFT: "Borrador",
  SCHEDULED: "Programada",
  RUNNING: "En curso",
  PAUSED: "Pausada",
  COMPLETED: "Completada",
  CANCELLED: "Cancelada",
};

const STATUS_VARIANTS: Record<CampaignStatus, "default" | "secondary" | "destructive" | "outline"> =
  {
    DRAFT: "outline",
    SCHEDULED: "secondary",
    RUNNING: "default",
    PAUSED: "secondary",
    COMPLETED: "secondary",
    CANCELLED: "destructive",
  };

/**
 * Vista de detalle de una campaña (lite scope — S4 PI-1).
 * Stats card + lifecycle buttons.
 */
export function CampaignDetailClient({ campaignId }: CampaignDetailClientProps) {
  const { data, isLoading, isError, refetch } = useCampaignDetailQuery(campaignId);

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4" aria-busy="true">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div role="alert" className="flex flex-col gap-3">
        <p className="text-muted-foreground">No se pudo cargar la campaña.</p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="text-primary hover:underline self-start text-sm"
        >
          Reintentar
        </button>
      </div>
    );
  }

  const { status } = data;

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{data.name}</h1>
          <Badge variant={STATUS_VARIANTS[status]}>{STATUS_LABELS[status]}</Badge>
        </div>
        {data.description && <p className="text-sm text-muted-foreground">{data.description}</p>}
        {data.segment_id && (
          <p className="text-xs text-muted-foreground">
            Segmento: <span className="font-mono">{data.segment_id}</span>
          </p>
        )}
      </div>

      {/* Lifecycle buttons */}
      <CampaignLifecycleButtons
        campaignId={campaignId}
        status={status}
        onStatusChange={() => void refetch()}
      />

      {/* Stats card */}
      <CampaignStatsCard campaignId={campaignId} />
    </div>
  );
}
