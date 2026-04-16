import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useGrowthStudioUrl } from "../use-growth-studio-url";

// ── Mocks ──────────────────────────────────────────────────────────────────────

const mockReplace = vi.fn();
const mockGet = vi.fn<(key: string) => string | null>().mockReturnValue(null);
const mockToString = vi.fn().mockReturnValue("");

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: mockReplace }),
  usePathname: () => "/tenant/growth-studio/atraccion-captura",
  useSearchParams: () => ({
    get: mockGet,
    toString: mockToString,
  }),
}));

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("useGrowthStudioUrl", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockReturnValue(null);
    mockToString.mockReturnValue("");
  });

  it("returns null urlChannel when no channel param", () => {
    const { result } = renderHook(() => useGrowthStudioUrl());
    expect(result.current.urlChannel).toBeNull();
  });

  it("reads channel slug from search params", () => {
    mockGet.mockReturnValue("meta-ads");
    const { result } = renderHook(() => useGrowthStudioUrl());
    expect(result.current.urlChannel).toBe("meta-ads");
  });

  it("openChannel updates search params via router.replace", () => {
    const { result } = renderHook(() => useGrowthStudioUrl());

    act(() => {
      result.current.openChannel("ig-organic");
    });

    expect(mockReplace).toHaveBeenCalledTimes(1);
    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).toContain("channel=ig-organic");
  });

  it("closeChannel removes channel param", () => {
    mockGet.mockReturnValue("meta-ads");
    mockToString.mockReturnValue("channel=meta-ads");

    const { result } = renderHook(() => useGrowthStudioUrl());

    act(() => {
      result.current.closeChannel();
    });

    expect(mockReplace).toHaveBeenCalledTimes(1);
    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).not.toContain("channel=");
  });

  it("openChannel preserves other search params", () => {
    mockToString.mockReturnValue("tab=overview");

    const { result } = renderHook(() => useGrowthStudioUrl());

    act(() => {
      result.current.openChannel("yt-organic");
    });

    const calledUrl = mockReplace.mock.calls[0][0] as string;
    expect(calledUrl).toContain("tab=overview");
    expect(calledUrl).toContain("channel=yt-organic");
  });

  it("uses router.replace not push (no history stack pollution)", () => {
    const { result } = renderHook(() => useGrowthStudioUrl());

    act(() => {
      result.current.openChannel("email-nurture");
    });

    // replace was called, not push
    expect(mockReplace).toHaveBeenCalledTimes(1);
  });
});
