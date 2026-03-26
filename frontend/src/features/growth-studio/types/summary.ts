export interface StageSummaryKpi {
  stage: string;
  mainKpi: number;
  mainLabel: string;
  mainUnit?: string;
  secondaryKpi: number;
  secondaryLabel: string;
  secondaryUnit?: string;
}

export interface BowtiesSummary {
  stages: StageSummaryKpi[];
  period: string;
  lastUpdated?: string;
}
