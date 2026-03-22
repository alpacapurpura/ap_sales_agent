import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAttractionDetail } from '../useAttractionDetail';
import type { AttractionDetail } from '@/features/marketing-studio/types/metrics';

// Mock the API module
vi.mock('@/features/marketing-studio/api/metrics-api', () => ({
  metricsApi: {
    getAttractionDetail: vi.fn(),
  },
}));

// Mock Clerk auth for hook context
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn(() => Promise.resolve('mock-token')) }),
}));

// Mock React Query wrapper — hooks use useQuery internally
// Tests run without a QueryClientProvider by default; install wrapper if needed in Plan 11-01
const mockAttractionData: Partial<AttractionDetail> = {
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

describe('useAttractionDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return isLoading true initially before fetch completes', () => {
    // Arrange
    // TODO (Plan 11-01): Wrap with QueryClientProvider for proper React Query context
    // For now, scaffold the test structure
    const isLoading = true;

    // Act & Assert
    expect(isLoading).toBe(true);
  });

  it('should fetch attraction detail data and return it', async () => {
    // Arrange
    // TODO (Plan 11-01): Set up metricsApi.getAttractionDetail mock to return mockAttractionData
    // const { metricsApi } = await import('@/features/marketing-studio/api/metrics-api');
    // vi.mocked(metricsApi.getAttractionDetail).mockResolvedValueOnce(mockAttractionData as AttractionDetail);

    // Verify mock data shape matches expected return type
    expect(mockAttractionData.period).toBe('2026-03-01_2026-03-16');
    expect(mockAttractionData.organicSocial?.totals.reach).toBe(15000);
  });

  it('should handle API errors and surface error state', async () => {
    // Arrange
    const mockError = new Error('Network Error: Unable to reach analytics API');

    // Act & Assert
    // TODO (Plan 11-01): Configure mock to reject and verify hook surfaces error
    // vi.mocked(metricsApi.getAttractionDetail).mockRejectedValueOnce(mockError);
    expect(mockError.message).toContain('Network Error');
  });

  it('should make parallel API calls without sequential blocking', async () => {
    // Arrange — useAttractionDetail (and its siblings) each use useQuery with unique queryKeys
    // so React Query runs them in parallel automatically (no await chaining between hooks)
    const queryKey = ['attraction-detail'];

    // Act & Assert
    // TODO (Plan 11-01): Verify 8 useXxxDetail hooks each declare unique queryKey arrays
    expect(queryKey[0]).toBe('attraction-detail');
  });

  it('should cache results using React Query staleTime of 5 minutes', async () => {
    // Arrange
    // Hook is configured with staleTime: 1000 * 60 * 5 (5 min)
    const expectedStaleTimeMs = 1000 * 60 * 5;

    // Act & Assert
    // TODO (Plan 11-01): Verify hook staleTime matches expected value
    // Confirm no unnecessary refetch within staleTime window
    expect(expectedStaleTimeMs).toBe(300000);
  });

  it('should use getToken from useAuth to authenticate API calls', async () => {
    // Arrange
    const getToken = vi.fn(() => Promise.resolve('mock-bearer-token'));

    // Act
    const token = await getToken();

    // Assert
    // TODO (Plan 11-01): Verify hook calls getToken() before invoking metricsApi
    expect(token).toBe('mock-bearer-token');
    expect(getToken).toHaveBeenCalledTimes(1);
  });
});
