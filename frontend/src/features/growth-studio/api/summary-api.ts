import { fetchClient } from "@/lib/http-client";
import { config } from "@/lib/config";
import { ENABLE_MOCKS } from "@/lib/mock-config";
import type { BowtiesSummary, StageSummaryKpi } from "../types/summary";

const API_URL = config.api.baseUrl;

function mapStageSummary(raw: any): StageSummaryKpi {
  return {
    stage: raw.stage,
    mainKpi: raw.main_kpi,
    mainLabel: raw.main_label,
    mainUnit: raw.main_unit ?? undefined,
    secondaryKpi: raw.secondary_kpi,
    secondaryLabel: raw.secondary_label,
    secondaryUnit: raw.secondary_unit ?? undefined,
  };
}

export async function fetchBowtiesSummary(token: string): Promise<BowtiesSummary> {
  if (ENABLE_MOCKS) return MOCK_BOWTIES_SUMMARY;

  const res = await fetchClient(`${API_URL}/api/v1/analytics/metrics/summary`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Summary API returned ${res.status}`);
  const raw = await res.json();

  return {
    stages: (raw.stages ?? []).map(mapStageSummary),
    period: raw.period,
    lastUpdated: raw.last_updated ?? undefined,
  };
}

export const MOCK_BOWTIES_SUMMARY: BowtiesSummary = {
  stages: [
    {
      stage: "attraction",
      mainKpi: 45000,
      mainLabel: "visitantes",
      secondaryKpi: 8,
      secondaryLabel: "canales activos",
    },
    {
      stage: "capture",
      mainKpi: 8500,
      mainLabel: "leads",
      secondaryKpi: 18.9,
      secondaryLabel: "tasa conversion",
      secondaryUnit: "%",
    },
    {
      stage: "nurture",
      mainKpi: 3200,
      mainLabel: "MQLs",
      secondaryKpi: 37.6,
      secondaryLabel: "engagement rate",
      secondaryUnit: "%",
    },
    {
      stage: "opportunity",
      mainKpi: 850,
      mainLabel: "SQLs",
      secondaryKpi: 26.6,
      secondaryLabel: "pipeline value",
      secondaryUnit: "%",
    },
    {
      stage: "sales",
      mainKpi: 1260000,
      mainLabel: "revenue",
      mainUnit: "$",
      secondaryKpi: 52.9,
      secondaryLabel: "conversion",
      secondaryUnit: "%",
    },
    {
      stage: "adoption",
      mainKpi: 88.9,
      mainLabel: "salud %",
      mainUnit: "%",
      secondaryKpi: 400,
      secondaryLabel: "activos",
    },
    {
      stage: "expansion",
      mainKpi: 42000,
      mainLabel: "net MRR",
      mainUnit: "$",
      secondaryKpi: 2.3,
      secondaryLabel: "churn rate",
      secondaryUnit: "%",
    },
    {
      stage: "evangelization",
      mainKpi: 1.8,
      mainLabel: "k-factor",
      secondaryKpi: 15.2,
      secondaryLabel: "conversion",
      secondaryUnit: "%",
    },
  ],
  period: "last_30_days",
  lastUpdated: "2026-03-14T03:15:00Z",
};
