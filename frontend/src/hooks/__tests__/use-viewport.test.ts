/**
 * Tests for useViewport hook.
 * Covers: SSR-safe initial null, breakpoint transitions, matchMedia mock.
 */
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { useViewport } from "../use-viewport";

// ── matchMedia mock factory ───────────────────────────────────────────────────

type MatchMediaListener = (e: MediaQueryListEvent) => void;

function mockMatchMedia(initialWidth: number) {
  const listeners = new Map<string, Set<MatchMediaListener>>();

  const matchMedia = vi.fn((query: string): MediaQueryList => {
    const matches = evaluateQuery(query, initialWidth);
    const mql = {
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_event: string, listener: MatchMediaListener) => {
        const existing = listeners.get(query) ?? new Set<MatchMediaListener>();
        existing.add(listener);
        listeners.set(query, existing);
      }),
      removeEventListener: vi.fn((_event: string, listener: MatchMediaListener) => {
        listeners.get(query)?.delete(listener);
      }),
      dispatchEvent: vi.fn(),
    } as unknown as MediaQueryList;
    return mql;
  });

  function fireChange(newWidth: number) {
    listeners.forEach((set, query) => {
      const matches = evaluateQuery(query, newWidth);
      const event = { matches, media: query } as MediaQueryListEvent;
      set.forEach((listener) => listener(event));
    });
  }

  return { matchMedia, fireChange };
}

function evaluateQuery(query: string, width: number): boolean {
  const minMatch = query.match(/\(min-width:\s*(\d+)px\)/);
  const maxMatch = query.match(/\(max-width:\s*(\d+)px\)/);
  if (minMatch) return width >= parseInt(minMatch[1], 10);
  if (maxMatch) return width <= parseInt(maxMatch[1], 10);
  return false;
}

describe("useViewport", () => {
  let originalMatchMedia: typeof window.matchMedia;
  let originalInnerWidth: number;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    originalInnerWidth = window.innerWidth;
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      value: originalInnerWidth,
    });
    vi.restoreAllMocks();
  });

  it("returns initial null width on SSR / before mount (no matchMedia)", () => {
    // Simulate SSR environment (no matchMedia)
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: undefined,
    });

    const { result } = renderHook(() => useViewport());

    // Initial state before any effect fires: SSR-safe
    expect(result.current.width).toBeNull();
    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
  });

  it("detects mobile breakpoint (<768px)", () => {
    const { matchMedia } = mockMatchMedia(500);
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: matchMedia,
    });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      value: 500,
    });

    const { result } = renderHook(() => useViewport());

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(false);
  });

  it("detects tablet breakpoint (768-1023px)", () => {
    const { matchMedia } = mockMatchMedia(900);
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: matchMedia,
    });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      value: 900,
    });

    const { result } = renderHook(() => useViewport());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(true);
    expect(result.current.isDesktop).toBe(false);
  });

  it("detects desktop breakpoint (>=1024px)", () => {
    const { matchMedia } = mockMatchMedia(1280);
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: matchMedia,
    });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      value: 1280,
    });

    const { result } = renderHook(() => useViewport());

    expect(result.current.isMobile).toBe(false);
    expect(result.current.isTablet).toBe(false);
    expect(result.current.isDesktop).toBe(true);
  });

  it("transitions from desktop to mobile on matchMedia change", () => {
    const { matchMedia, fireChange } = mockMatchMedia(1280);
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: matchMedia,
    });
    Object.defineProperty(window, "innerWidth", {
      writable: true,
      value: 1280,
    });

    const { result } = renderHook(() => useViewport());

    expect(result.current.isDesktop).toBe(true);

    act(() => {
      // Update innerWidth so the handler computes the new state correctly
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        value: 500,
      });
      fireChange(500);
    });

    expect(result.current.isMobile).toBe(true);
    expect(result.current.isDesktop).toBe(false);
  });
});
