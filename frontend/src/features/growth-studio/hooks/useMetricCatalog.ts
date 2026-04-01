import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';
import { metricsApi } from '../api/metrics-api';
import type { MetricCatalogEntry, MetricCatalog } from '../types/metrics';

export function useMetricCatalog() {
  const { getToken } = useAuth();

  const { data } = useQuery<MetricCatalog>({
    queryKey: ['metric-catalog'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error('No auth token');
      return metricsApi.getMetricCatalog(token);
    },
    staleTime: 1000 * 60 * 60, // 1-hour cache — catalog rarely changes
    gcTime: 1000 * 60 * 60 * 24,
  });

  const catalogByName = useMemo((): Record<string, MetricCatalogEntry> => {
    const map: Record<string, MetricCatalogEntry> = {};
    for (const entry of data?.metrics ?? []) {
      map[entry.name] = entry;
    }
    return map;
  }, [data]);

  return {
    catalog: data?.metrics ?? [],
    catalogByName,
    /** Returns catalog display_name or falls back to the provided fallback label. */
    getLabel: (name: string, fallback?: string): string =>
      catalogByName[name]?.display_name ?? fallback ?? name,
    /** True only for ADDITIVE metrics — safe to sum across channels/groups. */
    isAdditive: (name: string): boolean =>
      catalogByName[name]?.aggregation === 'additive',
  };
}
