import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAttractionDetail } from '../useStageDetail';
import type { AttractionDetail } from '@/features/growth-studio/types/metrics';

// ── Inline test helpers (avoid .tsx import from .ts) ─────────────────────────

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

const mockGetAttractionDetail = vi.fn();

vi.mock('@/features/growth-studio/api/metrics-api', () => ({
  metricsApi: {
    getAttractionDetail: (...args: unknown[]) => mockGetAttractionDetail(...args),
  },
}));

vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue('mock-test-token'),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock('../../components/metrics-dashboard/context/GrowthStudioContext', () => ({
  useGrowthStudioContext: () => ({
    selectedPeriod: 'last_30_days',
  }),
}));

// ── Test Data ────────────────────────────────────────────────────────────────

const mockAttractionData: AttractionDetail = {
  period: '2026-03-01_2026-03-16',
  organicSocial: {
    totals: { reach: 15000, engagement: 450 },
    channels: [],
  },
  ga4Search: {
    totals: { sessions: 3200 },
    channels: [],
  },
  paid: {
    totals: { impressions: 85000, spend: 150 },
    channels: [],
  },
  outbound: {
    totals: {},
    channels: [],
  },
};

// ── Tests ────────────────────────────────────────────────────────────────────

describe('useAttractionDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage for tenant ID
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

  it('returns loading state initially before fetch completes', () => {
    mockGetAttractionDetail.mockReturnValue(new Promise(() => {})); // never resolves
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useAttractionDetail(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('returns attraction detail data on successful fetch', async () => {
    mockGetAttractionDetail.mockResolvedValue(mockAttractionData);
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useAttractionDetail(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockAttractionData);
    expect(result.current.data?.period).toBe('2026-03-01_2026-03-16');
    expect(result.current.data?.organicSocial.totals.reach).toBe(15000);
  });

  it('surfaces error on failed fetch', async () => {
    const apiError = new Error('Network Error: Unable to reach analytics API');
    mockGetAttractionDetail.mockRejectedValue(apiError);
    const { wrapper } = createHookWrapper();

    const { result } = renderHook(() => useAttractionDetail(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Network Error');
  });

  it('passes the auth token and period to the API function', async () => {
    mockGetAttractionDetail.mockResolvedValue(mockAttractionData);
    const { wrapper } = createHookWrapper();

    renderHook(() => useAttractionDetail(), { wrapper });

    await waitFor(() => {
      expect(mockGetAttractionDetail).toHaveBeenCalled();
    });

    // createStageDetailHook calls apiFn(token, selectedPeriod)
    expect(mockGetAttractionDetail).toHaveBeenCalledWith('mock-test-token', 'last_30_days');
  });

  it('includes tenantId and period in the query key', async () => {
    mockGetAttractionDetail.mockResolvedValue(mockAttractionData);
    const { wrapper, queryClient } = createHookWrapper();

    renderHook(() => useAttractionDetail(), { wrapper });

    await waitFor(() => {
      expect(mockGetAttractionDetail).toHaveBeenCalled();
    });

    // Verify queryKey structure: ['attraction-detail', tenantId, period]
    const queryCache = queryClient.getQueryCache();
    const queries = queryCache.getAll();
    const attractionQuery = queries.find(q => q.queryKey[0] === 'attraction-detail');
    expect(attractionQuery).toBeDefined();
    expect(attractionQuery?.queryKey).toEqual(['attraction-detail', 'test-tenant-id', 'last_30_days']);
  });
});
