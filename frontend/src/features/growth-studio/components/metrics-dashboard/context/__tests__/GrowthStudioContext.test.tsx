import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { type ReactNode } from 'react';
import { GrowthStudioProvider, useGrowthStudioContext, SLUG_TO_STAGE, STAGE_TO_SLUG } from '../GrowthStudioContext';

// ── Mocks ──────────────────────────────────────────────────────────────────────

let currentPathname = '/tenant123/growth-studio/atraccion-captura';
const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockGet = vi.fn<(key: string) => string | null>().mockReturnValue(null);
const mockSearchParamsToString = vi.fn().mockReturnValue('');

vi.mock('next/navigation', () => ({
  usePathname: () => currentPathname,
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useSearchParams: () => ({
    get: mockGet,
    toString: mockSearchParamsToString,
  }),
}));

function wrapper({ children }: { children: ReactNode }) {
  return <GrowthStudioProvider>{children}</GrowthStudioProvider>;
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe('GrowthStudioContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    currentPathname = '/tenant123/growth-studio/atraccion-captura';
    mockGet.mockReturnValue(null);
    mockSearchParamsToString.mockReturnValue('');
  });

  describe('SLUG_TO_STAGE mapping', () => {
    it('maps all 5 stage slugs correctly', () => {
      expect(SLUG_TO_STAGE['atraccion-captura']).toBe('ATRACCION_CAPTURA');
      expect(SLUG_TO_STAGE['nutricion-oportunidad']).toBe('NUTRICION_OPORTUNIDAD');
      expect(SLUG_TO_STAGE['ventas']).toBe('VENTAS');
      expect(SLUG_TO_STAGE['adopcion']).toBe('ADOPCION');
      expect(SLUG_TO_STAGE['expansion-evangelizacion']).toBe('EXPANSION_EVANGELIZACION');
    });
  });

  describe('STAGE_TO_SLUG mapping', () => {
    it('maps all 5 stage IDs to slugs', () => {
      expect(STAGE_TO_SLUG.ATRACCION_CAPTURA).toBe('atraccion-captura');
      expect(STAGE_TO_SLUG.NUTRICION_OPORTUNIDAD).toBe('nutricion-oportunidad');
      expect(STAGE_TO_SLUG.VENTAS).toBe('ventas');
      expect(STAGE_TO_SLUG.ADOPCION).toBe('adopcion');
      expect(STAGE_TO_SLUG.EXPANSION_EVANGELIZACION).toBe('expansion-evangelizacion');
    });
  });

  describe('activeStage derivation', () => {
    it('derives activeStage from last-segment of stage URL', () => {
      currentPathname = '/tenant123/growth-studio/ventas';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });
      expect(result.current.activeStage).toBe('VENTAS');
    });

    it('derives activeStage for nested channel route (not the channelSlug)', () => {
      // When navigating to /tenant/growth-studio/atraccion-captura/meta-ads
      // activeStage should be ATRACCION_CAPTURA, not null (meta-ads is not a stage)
      currentPathname = '/tenant123/growth-studio/atraccion-captura/meta-ads';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });
      expect(result.current.activeStage).toBe('ATRACCION_CAPTURA');
    });

    it('derives activeStage for nested channel route under nutricion-oportunidad', () => {
      currentPathname = '/tenant123/growth-studio/nutricion-oportunidad/email-nurture';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });
      expect(result.current.activeStage).toBe('NUTRICION_OPORTUNIDAD');
    });

    it('returns null for unknown stage slug', () => {
      currentPathname = '/tenant123/growth-studio/unknown-stage';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });
      expect(result.current.activeStage).toBeNull();
    });
  });

  describe('handleOpenExpandedDashboard', () => {
    it('navigates to nested channel route via router.push', () => {
      currentPathname = '/tenant123/growth-studio/atraccion-captura';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleOpenExpandedDashboard('meta-ads');
      });

      expect(mockPush).toHaveBeenCalledTimes(1);
      expect(mockPush).toHaveBeenCalledWith(
        '/tenant123/growth-studio/atraccion-captura/meta-ads',
      );
    });

    it('uses correct stage slug for ventas', () => {
      currentPathname = '/tenant123/growth-studio/ventas';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleOpenExpandedDashboard('some-channel');
      });

      expect(mockPush).toHaveBeenCalledWith(
        '/tenant123/growth-studio/ventas/some-channel',
      );
    });

    it('falls back to atraccion-captura when no activeStage', () => {
      currentPathname = '/tenant123/growth-studio';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleOpenExpandedDashboard('ig-organic');
      });

      expect(mockPush).toHaveBeenCalledWith(
        '/tenant123/growth-studio/atraccion-captura/ig-organic',
      );
    });

    it('closes sidebars when navigating to expanded dashboard', () => {
      currentPathname = '/tenant123/growth-studio/atraccion-captura';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      // First open a channel sidebar
      act(() => {
        result.current.handleChannelClick({
          slug: 'meta-ads',
          name: 'Meta Ads',
          channelType: 'paid',
          sourceLabel: 'Meta',
          connected: true,
          providerName: 'meta',
          metrics: [],
        });
      });
      expect(result.current.channelSidebarOpen).toBe(true);

      // Now expand - should close sidebar
      act(() => {
        result.current.handleOpenExpandedDashboard('meta-ads');
      });
      expect(result.current.channelSidebarOpen).toBe(false);
      expect(result.current.selectedChannel).toBeNull();
    });
  });

  describe('handleChannelClick with URL sync', () => {
    it('opens channel sidebar and syncs URL', () => {
      currentPathname = '/tenant123/growth-studio/atraccion-captura';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleChannelClick({
          slug: 'meta-ads',
          name: 'Meta Ads',
          channelType: 'paid',
          sourceLabel: 'Meta',
          connected: true,
          providerName: 'meta',
          metrics: [],
        });
      });

      expect(result.current.channelSidebarOpen).toBe(true);
      expect(result.current.selectedChannel?.slug).toBe('meta-ads');
      // URL should be updated via replace
      expect(mockReplace).toHaveBeenCalledTimes(1);
      const calledUrl = mockReplace.mock.calls[0][0] as string;
      expect(calledUrl).toContain('channel=meta-ads');
    });

    it('ignores click on disconnected channel', () => {
      currentPathname = '/tenant123/growth-studio/atraccion-captura';
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleChannelClick({
          slug: 'tiktok',
          name: 'TikTok',
          channelType: 'organic_social',
          sourceLabel: 'TikTok',
          connected: false,
          providerName: undefined,
          metrics: [],
        });
      });

      expect(result.current.channelSidebarOpen).toBe(false);
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe('handleChannelSidebarClose with URL sync', () => {
    it('closes sidebar and removes channel from URL', () => {
      currentPathname = '/tenant123/growth-studio/atraccion-captura';
      mockSearchParamsToString.mockReturnValue('channel=meta-ads');
      const { result } = renderHook(() => useGrowthStudioContext(), { wrapper });

      act(() => {
        result.current.handleChannelSidebarClose();
      });

      expect(result.current.channelSidebarOpen).toBe(false);
      expect(result.current.selectedChannel).toBeNull();
      expect(mockReplace).toHaveBeenCalledTimes(1);
      const calledUrl = mockReplace.mock.calls[0][0] as string;
      expect(calledUrl).not.toContain('channel=');
    });
  });
});
