import type { StageSummary } from '../../../types/metrics';

/**
 * Derives a StageSummary from a per-stage detail API response, merging with the
 * mock StageSummary baseline when the API has not yet returned data.
 *
 * Progressive loading: each stage updates independently as its hook resolves.
 */
export function mergeStageData(
  base: StageSummary,
  apiData: unknown,
  isLoading: boolean,
  isError: boolean
): { summary: StageSummary; isLoading: boolean; isMock: boolean } {
  // If we have real API data, extract the main KPI based on stage id
  if (apiData != null && !isError) {
    const data = apiData as Record<string, unknown>;
    const kpis = (data.headerKpis ?? {}) as Record<string, unknown>;
    const miniFunnel = (data.miniFunnel ?? {}) as Record<string, unknown>;

    // Map each stage to its primary KPI field from backend
    let mainValue: number = base.mainKpi.value as number;
    let mainLabel: string = base.mainKpi.label;
    let mainUnit: string | undefined = base.mainKpi.unit;
    let secondaryValue: number = base.secondaryKpi.value as number;
    let secondaryUnit: string | undefined = base.secondaryKpi.unit;

    switch (base.id) {
      case 'ATRACCION': {
        const groups = ['organicSocial', 'ga4Search', 'paid', 'outbound'] as const;
        let totalVisitors = 0;
        for (const g of groups) {
          const group = (data[g] ?? {}) as Record<string, unknown>;
          const totals = (group.totals ?? {}) as Record<string, number>;
          totalVisitors += totals.reach ?? totals.sessions ?? totals.contacts ?? 0;
        }
        mainValue = totalVisitors;
        mainLabel = 'visitantes';
        mainUnit = undefined;

        let connectedCount = 0;
        for (const g of groups) {
          const group = (data[g] ?? {}) as Record<string, unknown>;
          const channels = (group.channels ?? []) as unknown[];
          connectedCount += channels.length;
        }
        secondaryValue = connectedCount;
        break;
      }
      case 'CAPTURA': {
        mainValue = (kpis.totalLeads ?? 0) as number;
        mainLabel = 'leads';
        mainUnit = undefined;
        secondaryValue = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        secondaryUnit = '%';
        break;
      }
      case 'NUTRICION': {
        mainValue = (kpis.totalMqls ?? 0) as number;
        mainLabel = 'MQLs';
        mainUnit = undefined;
        secondaryValue = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        secondaryUnit = '%';
        break;
      }
      case 'OPORTUNIDAD': {
        mainValue = (kpis.totalSqls ?? 0) as number;
        mainLabel = 'SQLs';
        mainUnit = undefined;
        secondaryValue = (kpis.conversionRate ?? (miniFunnel.conversionRate ?? 0)) as number;
        secondaryUnit = '%';
        break;
      }
      case 'VENTAS': {
        mainValue = (kpis.totalRevenue ?? 0) as number;
        const newCust = (kpis.newCustomers ?? 0) as number;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        mainLabel = 'revenue';
        mainUnit = '$';
        secondaryValue = rate > 0 ? rate : newCust;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
      case 'ADOPCION': {
        mainValue = (kpis.healthPct ?? 0) as number;
        const active = (kpis.activeCustomers ?? 0) as number;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        mainLabel = 'salud %';
        mainUnit = '%';
        secondaryValue = rate > 0 ? rate : active;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
      case 'EXPANSION': {
        mainValue = (kpis.netMrr ?? 0) as number;
        mainLabel = 'net MRR';
        mainUnit = '$';
        secondaryValue = (kpis.churnRatePct ?? (miniFunnel.conversionRate ?? 0)) as number;
        secondaryUnit = '%';
        break;
      }
      case 'EVANGELIZACION': {
        mainValue = (kpis.kFactor ?? 0) as number;
        mainLabel = 'k-factor';
        mainUnit = undefined;
        const rate = (miniFunnel.conversionRate ?? 0) as number;
        secondaryValue = rate;
        secondaryUnit = rate > 0 ? '%' : undefined;
        break;
      }
    }

    return {
      summary: {
        ...base,
        mainKpi: { label: mainLabel, value: mainValue, unit: mainUnit },
        secondaryKpi: { label: base.secondaryKpi.label, value: secondaryValue, unit: secondaryUnit },
      },
      isLoading: false,
      isMock: false,
    };
  }

  return {
    summary: base,
    isLoading,
    isMock: !isLoading, // if not loading and no data, we're showing fallback mock
  };
}