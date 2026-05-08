"use client";

import { STAGE_SUMMARIES } from "../../api/stage-summaries-fallback";
import { useBowtiesSummary } from "../../hooks/use-bowties-summary";

import type { StageId, StageSummary } from "../../types/metrics";
import type { StageSummaryKpi } from "../../types/summary";

/**
 * Tier 0 — Bowtie summary (1 request, lightest data tier).
 *
 * Fetches the lightweight Bowtie summary and composes the 5
 * composite StageSummary entries shown in the Bowtie row.
 *
 * Canonical location: features/growth-studio/pages/tiers/tier0-summary.ts
 * Moved from: components/metrics-dashboard/hooks/use-stage-summaries.ts (T-3)
 *
 * Replaces the previous approach of calling all 8 detail hooks eagerly.
 * Detail data is now fetched on-demand only when the user navigates
 * into a specific stage.
 */
export function useTier0Summary() {
  const { data: summary, isLoading, isError } = useBowtiesSummary();

  // Build a lookup: stage name -> StageSummaryKpi
  const stageMap = new Map<string, StageSummaryKpi>();
  if (summary) {
    for (const s of summary.stages) {
      stageMap.set(s.stage, s);
    }
  }

  const baseSummaries = STAGE_SUMMARIES;
  const isMock = !summary || isError;

  // Helper to get KPI from summary or fallback to mock baseline
  function getKpi(stage: string, base: StageSummary): StageSummary {
    const kpi = stageMap.get(stage);
    if (!kpi) return base;
    return {
      ...base,
      mainKpi: { label: kpi.mainLabel, value: kpi.mainKpi, unit: kpi.mainUnit },
      secondaryKpi: { label: kpi.secondaryLabel, value: kpi.secondaryKpi, unit: kpi.secondaryUnit },
    };
  }

  const attraction = getKpi("attraction", baseSummaries[0]);
  const capture = getKpi("capture", baseSummaries[1]);
  const nurture = getKpi("nurture", baseSummaries[2]);
  const opportunity = getKpi("opportunity", baseSummaries[3]);
  const sales = getKpi("sales", baseSummaries[4]);
  const adoption = getKpi("adoption", baseSummaries[5]);
  const expansion = getKpi("expansion", baseSummaries[6]);
  const evangelization = getKpi("evangelization", baseSummaries[7]);

  const enrichedSummaries: StageSummary[] = [
    {
      id: "ATRACCION_CAPTURA",
      order: 0,
      label: "Atraccion & Captura",
      description: "Etapa 1 y 2 - Trafico y visitantes convertidos a leads",
      mainKpi: attraction.mainKpi,
      secondaryKpi: { label: "leads", value: capture.mainKpi.value, unit: capture.mainKpi.unit },
      hasDetail: true,
    },
    {
      id: "NUTRICION_OPORTUNIDAD",
      order: 1,
      label: "Nutricion & Oportunidad",
      description: "Etapa 3 y 4 - Calentamiento de leads y generacion de intenciones de compra",
      mainKpi: nurture.mainKpi,
      secondaryKpi: {
        label: "SQLs",
        value: opportunity.mainKpi.value,
        unit: opportunity.mainKpi.unit,
      },
      hasDetail: true,
    },
    sales,
    adoption,
    {
      id: "EXPANSION_EVANGELIZACION",
      order: 4,
      label: "Expansion & Evangelizacion",
      description: "Etapa 5 y 6 - Retencion, crecimiento de LTV y referidos",
      mainKpi: expansion.mainKpi,
      secondaryKpi: {
        label: "k-factor",
        value: evangelization.mainKpi.value,
        unit: evangelization.mainKpi.unit,
      },
      hasDetail: true,
    },
  ];

  const allLoading = isLoading;

  const loadingMap: Record<StageId, boolean> = {
    ATRACCION_CAPTURA: allLoading,
    ATRACCION: false,
    CAPTURA: false,
    NUTRICION_OPORTUNIDAD: allLoading,
    NUTRICION: false,
    OPORTUNIDAD: false,
    VENTAS: allLoading,
    ADOPCION: allLoading,
    EXPANSION_EVANGELIZACION: allLoading,
    EXPANSION: false,
    EVANGELIZACION: false,
  };

  const mockMap: Record<StageId, boolean> = {
    ATRACCION_CAPTURA: isMock,
    ATRACCION: false,
    CAPTURA: false,
    NUTRICION_OPORTUNIDAD: isMock,
    NUTRICION: false,
    OPORTUNIDAD: false,
    VENTAS: isMock,
    ADOPCION: isMock,
    EXPANSION_EVANGELIZACION: isMock,
    EXPANSION: false,
    EVANGELIZACION: false,
  };

  return { enrichedSummaries, loadingMap, mockMap };
}
