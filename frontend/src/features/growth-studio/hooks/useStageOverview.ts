'use client';

import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { stageOverviewApi } from '../api/stage-overview-api';
import { useGrowthStudioContext } from '../components/metrics-dashboard/context/GrowthStudioContext';
import type { StageOverview } from '../types/metrics';

interface UseStageOverviewOptions {
  /** When false, the query will not execute. Defaults to true. */
  enabled?: boolean;
}

/**
 * Fetches the lightweight stage overview (Tier 1) — header KPIs + channel list
 * with 1 headline metric per channel.
 *
 * This is the first data tier that renders immediately when entering a stage.
 * Full detail data (Tier 2) loads per-group on viewport visibility.
 */
export function useStageOverview(stage: string, options?: UseStageOverviewOptions) {
  const { getToken } = useAuth();
  const tenantId = typeof window !== 'undefined'
    ? localStorage.getItem('x-tenant-id') : null;
  const { selectedPeriod } = useGrowthStudioContext();

  return useQuery<StageOverview>({
    queryKey: ['stage-overview', tenantId, stage, selectedPeriod],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return stageOverviewApi.getStageOverview(token, stage, selectedPeriod);
    },
    staleTime: 1000 * 60 * 5, // 5 min — same as detail hooks
    enabled: options?.enabled ?? true,
  });
}
