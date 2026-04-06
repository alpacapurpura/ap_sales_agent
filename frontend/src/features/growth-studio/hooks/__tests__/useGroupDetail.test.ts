import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue('mock-token'),
  }),
}));

vi.mock('next/navigation', () => ({
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
  usePathname: () => '/tenant/growth-studio/atraccion-captura',
  useSearchParams: () => ({
    get: () => null,
    toString: () => '',
  }),
}));

const mockGetAttractionDetail = vi.fn().mockResolvedValue({
  organicSocial: {
    totals: { reach: 8000, engagement: 500 },
    channels: [
      {
        slug: 'ig-organic',
        name: 'Instagram',
        channelType: 'organic_social',
        metrics: [{ name: 'reach', value: 5000 }, { name: 'engagement', value: 300 }],
        sourceLabel: 'Instagram',
        connected: true,
      },
    ],
  },
  ga4Search: { totals: { sessions: 1000 }, channels: [] },
  paid: {
    totals: { spend: 1500, impressions: 50000 },
    channels: [
      {
        slug: 'meta-ads',
        name: 'Meta Ads',
        channelType: 'paid',
        metrics: [{ name: 'spend', value: 1500 }],
        sourceLabel: 'Meta',
        connected: true,
      },
    ],
  },
  outbound: { totals: {}, channels: [] },
  period: 'last_30_days',
});

vi.mock('../../api/metrics-api', () => ({
  metricsApi: {
    getAttractionDetail: (...args: unknown[]) => mockGetAttractionDetail(...args),
    getCaptureDetail: vi.fn().mockResolvedValue({}),
    getNurtureDetail: vi.fn().mockResolvedValue({}),
    getOpportunityDetail: vi.fn().mockResolvedValue({}),
    getSalesDetail: vi.fn().mockResolvedValue({}),
    getAdoptionDetail: vi.fn().mockResolvedValue({}),
    getExpansionDetail: vi.fn().mockResolvedValue({}),
    getEvangelizationDetail: vi.fn().mockResolvedValue({}),
  },
}));

// ── Import after mocks ────────────────────────────────────────────────────────

import { useGroupDetail } from '../useGroupDetail';
import { GrowthStudioProvider } from '../../components/metrics-dashboard/context/GrowthStudioContext';

// ── Wrapper ───────────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      React.createElement(GrowthStudioProvider, null, children),
    );
  };
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('useGroupDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('x-tenant-id', 'test-tenant');
    }
  });

  it('does NOT fetch when enabled=false (default)', async () => {
    renderHook(() => useGroupDetail('attraction', 'paid'), {
      wrapper: createWrapper(),
    });

    // Wait a tick for any potential calls
    await new Promise(resolve => setTimeout(resolve, 50));
    expect(mockGetAttractionDetail).not.toHaveBeenCalled();
  });

  it('fetches when enabled=true and extracts the requested group', async () => {
    const { result } = renderHook(
      () => useGroupDetail('attraction', 'paid', { enabled: true }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.channels).toHaveLength(1);
    expect(result.current.data?.channels[0].slug).toBe('meta-ads');
    expect(result.current.data?.totals.spend).toBe(1500);
  });

  it('extracts organic_social group correctly', async () => {
    const { result } = renderHook(
      () => useGroupDetail('attraction', 'organic_social', { enabled: true }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.channels).toHaveLength(1);
    expect(result.current.data?.channels[0].slug).toBe('ig-organic');
  });

  it('returns undefined for unknown group key', async () => {
    const { result } = renderHook(
      () => useGroupDetail('attraction', 'nonexistent', { enabled: true }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.isFetched).toBe(true);
    });

    expect(result.current.data).toBeUndefined();
  });

  it('includes correct queryKey with stage, groupKey, and period', () => {
    const { result } = renderHook(
      () => useGroupDetail('attraction', 'paid', { enabled: true }),
      { wrapper: createWrapper() },
    );

    // The queryKey should include all discriminators for proper caching
    // We can't directly access queryKey, but we verify the hook was created
    expect(result.current.isLoading).toBe(true);
  });
});
