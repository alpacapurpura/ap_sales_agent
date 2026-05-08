/**
 * T-2 Scenario 2 — useCopilotOffset consumes COPILOT_WIDTHS SSoT.
 *
 * Validates that:
 *  1. Hook return value per sidebarState === COPILOT_WIDTHS derived totals.
 *  2. Mobile viewport returns 0 (no offset).
 *  3. Deprecated aliases COPILOT_OPEN_WIDTH + COPILOT_RAIL_WIDTH re-export
 *     from the module and resolve to the SSoT values.
 *  4. sidebarState API (3-state) replaces legacy isOpen boolean.
 */
import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { COPILOT_WIDTHS } from "@/features/copilot/lib/copilot-shell-widths";

// ── Mocks ────────────────────────────────────────────────────────────

// Mock useCopilotStore to expose sidebarState
vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: vi.fn(),
}));

// Mock useViewport — defaults to desktop (non-mobile)
vi.mock("@/hooks/use-viewport", () => ({
  useViewport: vi.fn(),
}));

import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { useViewport } from "@/hooks/use-viewport";
import { useCopilotOffset, COPILOT_OPEN_WIDTH, COPILOT_RAIL_WIDTH } from "@/hooks/use-copilot-offset";

const mockUseCopilotStore = vi.mocked(useCopilotStore);
const mockUseViewport = vi.mocked(useViewport);

/** Helper: set up useCopilotStore selector mock for sidebarState */
function mockSidebarState(state: "collapsed" | "rail" | "full") {
  // useCopilotStore is called with a selector fn; return the sidebarState
  mockUseCopilotStore.mockImplementation((selector) => {
    const fakeStore = { sidebarState: state };
    return selector(fakeStore as Parameters<typeof selector>[0]);
  });
}

/** Helper: set up useViewport mock */
function mockViewport(isMobile: boolean) {
  mockUseViewport.mockReturnValue({
    isMobile,
    isTablet: false,
    isDesktop: !isMobile,
    width: isMobile ? 375 : 1440,
  });
}

beforeEach(() => {
  // Default: desktop, copilot collapsed
  mockViewport(false);
  mockSidebarState("collapsed");
});

afterEach(() => {
  vi.clearAllMocks();
});

// ── COPILOT_WIDTHS SSoT sanity (load-bearing) ─────────────────────

describe("COPILOT_WIDTHS SSoT values", () => {
  it("expanded (rail state offset) equals 460", () => {
    expect(COPILOT_WIDTHS.expanded).toBe(460);
  });
  it("collapsed (rail-only offset) equals 60", () => {
    expect(COPILOT_WIDTHS.collapsed).toBe(60);
  });
  it("max (full state offset) equals 680", () => {
    expect(COPILOT_WIDTHS.max).toBe(680);
  });
});

// ── useCopilotOffset per sidebarState ────────────────────────────

describe("useCopilotOffset — sidebarState 3-state API", () => {
  it("returns COPILOT_WIDTHS.collapsed (60) when sidebarState is 'collapsed'", () => {
    mockSidebarState("collapsed");
    mockViewport(false);

    const { result } = renderHook(() => useCopilotOffset());
    expect(result.current).toBe(COPILOT_WIDTHS.collapsed);
    expect(result.current).toBe(60);
  });

  it("returns COPILOT_WIDTHS.expanded (460) when sidebarState is 'rail'", () => {
    mockSidebarState("rail");
    mockViewport(false);

    const { result } = renderHook(() => useCopilotOffset());
    expect(result.current).toBe(COPILOT_WIDTHS.expanded);
    expect(result.current).toBe(460);
  });

  it("returns COPILOT_WIDTHS.max (680) when sidebarState is 'full'", () => {
    mockSidebarState("full");
    mockViewport(false);

    const { result } = renderHook(() => useCopilotOffset());
    expect(result.current).toBe(COPILOT_WIDTHS.max);
    expect(result.current).toBe(680);
  });

  it("returns 0 on mobile regardless of sidebarState", () => {
    mockSidebarState("rail");
    mockViewport(true);

    const { result } = renderHook(() => useCopilotOffset());
    expect(result.current).toBe(0);
  });

  it("returns 0 on mobile even when sidebarState is 'full'", () => {
    mockSidebarState("full");
    mockViewport(true);

    const { result } = renderHook(() => useCopilotOffset());
    expect(result.current).toBe(0);
  });
});

// ── Deprecated aliases ────────────────────────────────────────────

describe("@deprecated re-exports resolve to SSoT values", () => {
  it("COPILOT_OPEN_WIDTH resolves to COPILOT_WIDTHS.expanded (460)", () => {
    // Previously 380 — now aligned with SSoT
    expect(COPILOT_OPEN_WIDTH).toBe(COPILOT_WIDTHS.expanded);
    expect(COPILOT_OPEN_WIDTH).toBe(460);
  });

  it("COPILOT_RAIL_WIDTH resolves to COPILOT_WIDTHS.collapsed (60)", () => {
    expect(COPILOT_RAIL_WIDTH).toBe(COPILOT_WIDTHS.collapsed);
    expect(COPILOT_RAIL_WIDTH).toBe(60);
  });
});
