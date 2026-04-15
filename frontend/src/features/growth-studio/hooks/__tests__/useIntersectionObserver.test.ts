import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── IntersectionObserver mock ──────────────────────────────────────────────────

type IntersectionCallback = (entries: Partial<IntersectionObserverEntry>[]) => void;

let mockCallback: IntersectionCallback | null = null;
const mockObserve = vi.fn();
const mockUnobserve = vi.fn();
const mockDisconnect = vi.fn();

class MockIntersectionObserver {
  constructor(
    callback: IntersectionCallback,
    public options?: IntersectionObserverInit,
  ) {
    mockCallback = callback;
  }
  observe = mockObserve;
  unobserve = mockUnobserve;
  disconnect = mockDisconnect;
  root = null;
  rootMargin = "";
  thresholds: number[] = [];
  takeRecords = () => [] as IntersectionObserverEntry[];
}

const OriginalIO = globalThis.IntersectionObserver;

beforeEach(() => {
  mockCallback = null;
  vi.clearAllMocks();
  globalThis.IntersectionObserver =
    MockIntersectionObserver as unknown as typeof IntersectionObserver;
});

afterEach(() => {
  globalThis.IntersectionObserver = OriginalIO;
});

// ── Tests ──────────────────────────────────────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/consistent-type-imports
let useIntersectionObserver: typeof import("../useIntersectionObserver").useIntersectionObserver;

beforeEach(async () => {
  // Re-import to pick up mock
  const mod = await import("../useIntersectionObserver");
  useIntersectionObserver = mod.useIntersectionObserver;
});

describe("useIntersectionObserver", () => {
  it("returns isVisible=false initially", () => {
    const { result } = renderHook(() => useIntersectionObserver());
    expect(result.current.isVisible).toBe(false);
  });

  it("returns a ref callback", () => {
    const { result } = renderHook(() => useIntersectionObserver());
    expect(typeof result.current.ref).toBe("function");
  });

  it("observes the element when ref is attached", () => {
    const { result } = renderHook(() => useIntersectionObserver());
    const element = document.createElement("div");

    act(() => {
      result.current.ref(element);
    });

    expect(mockObserve).toHaveBeenCalledWith(element);
  });

  it("returns isVisible=true when element enters viewport", () => {
    const { result } = renderHook(() => useIntersectionObserver());
    const element = document.createElement("div");

    act(() => {
      result.current.ref(element);
    });

    act(() => {
      mockCallback?.([{ isIntersecting: true }]);
    });

    expect(result.current.isVisible).toBe(true);
  });

  it("stays visible once seen (no flicker on scroll out)", () => {
    const { result } = renderHook(() => useIntersectionObserver());
    const element = document.createElement("div");

    act(() => {
      result.current.ref(element);
    });

    act(() => {
      mockCallback?.([{ isIntersecting: true }]);
    });
    expect(result.current.isVisible).toBe(true);

    // Leave viewport — should STAY visible (once-mode)
    act(() => {
      mockCallback?.([{ isIntersecting: false }]);
    });
    expect(result.current.isVisible).toBe(true);
  });

  it("disconnects on unmount", () => {
    const { unmount } = renderHook(() => useIntersectionObserver());
    unmount();
    expect(mockDisconnect).toHaveBeenCalled();
  });
});
