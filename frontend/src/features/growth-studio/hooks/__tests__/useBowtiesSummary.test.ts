import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useBowtiesSummary } from '../useBowtiesSummary';
import type { BowtiesSummary } from '@/features/growth-studio/types/summary';

// ── Inline test helpers ──────────────────────────────────────────────────────

function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

function createHookWrapper() {
  const queryClient = createTestQueryClient();
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  }
  return { wrapper: Wrapper, queryClient };
}

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockFetchBowtiesSummary = vi.fn();

vi.mock('@/features/growth-studio/api/summary-api', () => ({
  fetchBowtiesSummary: (...args: unknown[]) => mockFetchBowtiesSummary(...args),
}));

vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue('mock-test-token'),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// ── Test Data ────────────────────────────────────────────────────────────────

const mockSummaryData: BowtiesSummary = {
  stages: [
    { stage: 'attraction', mainKpi: 45000, mainLabel: 'visitantes', secondaryKpi: 8, secondaryLabel: 'canales activos' },
    { stage: 'capture', mainKpi: 8500, mainLabel: 'leads', secondaryKpi: 18.9, secondaryLabel: 'tasa conversion', secondaryUnit: '%' },
    { stage: 'nurture', mainKpi: 3200, mainLabel: 'MQLs', secondaryKpi: 37.6, secondaryLabel: 'engagement rate', secondaryUnit: '%' },
    { stage: 'opportunity', mainKpi: 850, mainLabel: 'SQLs', secondaryKpi: 26.6, secondaryLabel: 'pipeline value', secondaryUnit: '%' },
    { stage: 'sales', mainKpi: 1260000, mainLabel: 'revenue', mainUnit: '$', secondaryKpi: 52.9, secondaryLabel: 'conversion', secondaryUnit: '%' },
    { stage: 'adoption', mainKpi: 88.9, mainLabel: 'salud %', mainUnit: '%', secondaryKpi: 400, secondaryLabel: 'activos' },
    { stage: 'expansion', mainKpi: 42000, mainLabel: 'net MRR', mainUnit: '$', secondaryKpi: 2.3, secondaryLabel: 'churn rate', secondaryUnit: '%' },
    { stage: 'evangelization', mainKpi: 1.8, mainLabel: 'k-factor', secondaryKpi: 15.2, secondaryLabel: 'conversion', secondaryUnit: '%' },
  ],
  period: 'last_30_days',
  lastUpdated: '2026-03-14T03:15:00Z',
};

// ── Tests ────────────────────────────────────────────────────────────────────

describe('useBowtiesSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(globalThis, 'localStorage', {
      value: {
        getItem: vi.fn().mockReturnValue('test-tenant-id'),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
        length: 0,
        key: vi.fn(),
      },
      writable: true,
      configurable: true,
    });
  });

  it('returns loading state initially', () => {
    mockFetchBowtiesSummary.mockReturnValue(new Promise(() => {})); // never resolves
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('returns summary data on successful fetch', async () => {
    mockFetchBowtiesSummary.mockResolvedValue(mockSummaryData);
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockSummaryData);
    expect(result.current.data?.stages).toHaveLength(8);
    expect(result.current.data?.period).toBe('last_30_days');
    expect(result.current.data?.stages[0].stage).toBe('attraction');
    expect(result.current.data?.stages[0].mainKpi).toBe(45000);
  });

  it('surfaces error on failed fetch', async () => {
    const apiError = new Error('Summary API returned 500');
    mockFetchBowtiesSummary.mockRejectedValue(apiError);
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Summary API returned 500');
  });

  it('passes the auth token to fetchBowtiesSummary', async () => {
    mockFetchBowtiesSummary.mockResolvedValue(mockSummaryData);
    const { wrapper } = createHookWrapper();

    renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(mockFetchBowtiesSummary).toHaveBeenCalled();
    });

    expect(mockFetchBowtiesSummary).toHaveBeenCalledWith('mock-test-token');
  });

  it('includes tenantId in the query key', async () => {
    mockFetchBowtiesSummary.mockResolvedValue(mockSummaryData);
    const { wrapper, queryClient } = createHookWrapper();

    renderHook(() => useBowtiesSummary(), { wrapper });

    await waitFor(() => {
      expect(mockFetchBowtiesSummary).toHaveBeenCalled();
    });

    const queryCache = queryClient.getQueryCache();
    const queries = queryCache.getAll();
    const summaryQuery = queries.find(q => q.queryKey[0] === 'bowties-summary');
    expect(summaryQuery).toBeDefined();
    expect(summaryQuery?.queryKey).toEqual(['bowties-summary', 'test-tenant-id']);
  });
});
