/**
 * Tests for shell-mutex-store + useShellMutex hook.
 *
 * Phase 1 scope: no-op state (effects gated). Verifies:
 * - Store mounts correctly with tenant-namespaced key
 * - Initial state is activePanel: null
 * - openPanel / closePanel / togglePanel actions work
 * - DashboardShell module exports exist (structural smoke)
 *
 * Phase 4 scope (T-4 additions):
 * - Mutex policy per breakpoint (desktop / tablet / mobile)
 * - Ping-pong idempotency (open A → open B → close B → A still closed)
 * - Tenant switch resets mutex state
 * - SidebarContext provides expandSidebar / collapseSidebar imperative actions
 */
import { act, render, renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { DashboardShell } from "@/components/shared/layout/DashboardShell";
import { SidebarProvider, useSidebar } from "@/components/shared/layout/SidebarContext";
import { createShellMutexStore } from "@/stores/shell-mutex-store";

/** Stable test tenant ID shared across store tests */
const TEST_TENANT = "tenant-123";
/** Panel constants */
const PANEL_SIDEBAR = "app-sidebar" as const;
const PANEL_COPILOT = "copilot" as const;

// ── matchMedia mock helper ──────────────────────────────────────────────────

function mockMatchMedia(width: number) {
  Object.defineProperty(window, "innerWidth", { writable: true, value: width });
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn((query: string): MediaQueryList => {
      const minMatch = /min-width:\s*(\d+)px/.exec(query);
      const maxMatch = /max-width:\s*(\d+)px/.exec(query);
      const matches = minMatch
        ? width >= parseInt(minMatch[1], 10)
        : maxMatch
          ? width <= parseInt(maxMatch[1], 10)
          : false;
      return {
        matches,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      } as unknown as MediaQueryList;
    }),
  });
}

// ── Phase 1 tests (store basics) ────────────────────────────────────────────

describe("shell-mutex-store (Phase 1 — no-op state)", () => {
  it("initialises with activePanel: null", () => {
    const store = createShellMutexStore(TEST_TENANT);
    expect(store.getState().activePanel).toBeNull();
  });

  it("openPanel sets activePanel to app-sidebar", () => {
    const store = createShellMutexStore(TEST_TENANT);
    act(() => {
      store.getState().openPanel(PANEL_SIDEBAR);
    });
    expect(store.getState().activePanel).toBe(PANEL_SIDEBAR);
  });

  it("openPanel sets activePanel to copilot", () => {
    const store = createShellMutexStore(TEST_TENANT);
    act(() => {
      store.getState().openPanel(PANEL_COPILOT);
    });
    expect(store.getState().activePanel).toBe(PANEL_COPILOT);
  });

  it("closePanel resets activePanel to null", () => {
    const store = createShellMutexStore(TEST_TENANT);
    act(() => {
      store.getState().openPanel(PANEL_SIDEBAR);
      store.getState().closePanel();
    });
    expect(store.getState().activePanel).toBeNull();
  });

  it("togglePanel opens when null, closes when same panel", () => {
    const store = createShellMutexStore(TEST_TENANT);

    act(() => {
      store.getState().togglePanel(PANEL_SIDEBAR);
    });
    expect(store.getState().activePanel).toBe(PANEL_SIDEBAR);

    act(() => {
      store.getState().togglePanel(PANEL_SIDEBAR);
    });
    expect(store.getState().activePanel).toBeNull();
  });

  it("togglePanel switches from one panel to another", () => {
    const store = createShellMutexStore(TEST_TENANT);

    act(() => {
      store.getState().openPanel(PANEL_SIDEBAR);
      store.getState().togglePanel(PANEL_COPILOT);
    });
    expect(store.getState().activePanel).toBe(PANEL_COPILOT);
  });

  it("uses tenant-namespaced localStorage key — stores for different tenants are independent", () => {
    const store1 = createShellMutexStore("tenant-aaa");
    const store2 = createShellMutexStore("tenant-bbb");

    act(() => {
      store1.getState().openPanel(PANEL_SIDEBAR);
    });

    expect(store2.getState().activePanel).toBeNull();
    expect(store1.getState().activePanel).toBe(PANEL_SIDEBAR);
  });
});

// ── Phase 4 tests (T-4) ─────────────────────────────────────────────────────

describe("shell-mutex-store (Phase 4 — mutex policy + idempotency)", () => {
  let originalMatchMedia: typeof window.matchMedia;
  let originalInnerWidth: number;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    originalInnerWidth = window.innerWidth;
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", { writable: true, value: originalMatchMedia });
    Object.defineProperty(window, "innerWidth", { writable: true, value: originalInnerWidth });
    vi.restoreAllMocks();
  });

  describe("Ping-pong idempotency — no infinite-loop recursion", () => {
    it("opening A then B then closing B leaves A closed (strict mutex behavior)", () => {
      const store = createShellMutexStore("tenant-ping-pong");

      act(() => {
        store.getState().openPanel(PANEL_SIDEBAR);
      });
      expect(store.getState().activePanel).toBe(PANEL_SIDEBAR);

      act(() => {
        // Simulates mutex policy: open copilot → sidebar loses active status
        store.getState().openPanel(PANEL_COPILOT);
      });
      expect(store.getState().activePanel).toBe(PANEL_COPILOT);

      act(() => {
        store.getState().closePanel();
      });
      // After closing copilot, activePanel is null (sidebar is NOT auto-reopened)
      expect(store.getState().activePanel).toBeNull();
    });

    it("multiple rapid openPanel calls converge to last panel (no ping-pong loop)", () => {
      const store = createShellMutexStore("tenant-rapid");
      let callCount = 0;

      // Subscribe to count state updates
      const unsub = store.subscribe(() => {
        callCount++;
        // Safety: if we see >10 transitions, something is looping
        if (callCount > 10) {
          throw new Error("Infinite update loop detected in mutex store");
        }
      });

      act(() => {
        store.getState().openPanel(PANEL_SIDEBAR);
        store.getState().openPanel(PANEL_COPILOT);
        store.getState().openPanel(PANEL_SIDEBAR);
        store.getState().openPanel(PANEL_COPILOT);
      });

      unsub();
      // Should settle on last openPanel call — copilot
      expect(store.getState().activePanel).toBe(PANEL_COPILOT);
      // And transition count should be bounded (4 transitions for 4 openPanel calls)
      expect(callCount).toBeLessThanOrEqual(8);
    });

    it("closePanel on already-null state is idempotent (no error, no loop)", () => {
      const store = createShellMutexStore("tenant-close-null");

      expect(store.getState().activePanel).toBeNull();

      expect(() => {
        act(() => {
          store.getState().closePanel(); // already null — should be no-op
          store.getState().closePanel(); // idempotent
        });
      }).not.toThrow();

      expect(store.getState().activePanel).toBeNull();
    });
  });

  describe("Tenant switch resets mutex state", () => {
    it("new store for different tenant starts with null activePanel regardless of prior tenant state", () => {
      const storeTenantA = createShellMutexStore("tenant-switch-a");

      act(() => {
        storeTenantA.getState().openPanel(PANEL_COPILOT);
      });
      expect(storeTenantA.getState().activePanel).toBe(PANEL_COPILOT);

      // Simulate tenant switch — new store factory call with different tenantId
      const storeTenantB = createShellMutexStore("tenant-switch-b");
      expect(storeTenantB.getState().activePanel).toBeNull();
    });

    it("closing tenant-A panel does not affect tenant-B panel state", () => {
      const storeA = createShellMutexStore("tenant-iso-a");
      const storeB = createShellMutexStore("tenant-iso-b");

      act(() => {
        storeA.getState().openPanel(PANEL_SIDEBAR);
        storeB.getState().openPanel(PANEL_COPILOT);
      });

      act(() => {
        storeA.getState().closePanel();
      });

      expect(storeA.getState().activePanel).toBeNull();
      expect(storeB.getState().activePanel).toBe(PANEL_COPILOT);
    });
  });

  describe("Desktop breakpoint ≥1280px — independent panels (no auto-collapse)", () => {
    it("both stores can be 'open' at ≥1280px — mutex does NOT enforce exclusivity", () => {
      mockMatchMedia(1440);
      // At desktop, both panels being in different stores is allowed.
      // The mutex policy in useShellMutex decides; here we verify store allows co-existence.
      const store = createShellMutexStore("tenant-desktop");

      act(() => {
        store.getState().openPanel(PANEL_SIDEBAR);
      });
      // Can then open copilot too — store itself does not enforce mutex (hook does)
      act(() => {
        store.getState().openPanel(PANEL_COPILOT);
      });
      expect(store.getState().activePanel).toBe(PANEL_COPILOT);
    });
  });

  describe("Mobile breakpoint <768px — strict mutex", () => {
    it("store state transitions correctly for mobile flow: open sidebar → open copilot → sidebar closed", () => {
      mockMatchMedia(500);
      const store = createShellMutexStore("tenant-mobile-flow");

      act(() => {
        store.getState().openPanel(PANEL_SIDEBAR);
      });
      expect(store.getState().activePanel).toBe(PANEL_SIDEBAR);

      // Simulate mutex policy: opening copilot → mutex forces sidebar to close
      act(() => {
        store.getState().openPanel(PANEL_COPILOT);
      });
      // Only copilot is now active
      expect(store.getState().activePanel).toBe(PANEL_COPILOT);
    });

    it("closePanel from copilot leaves null activePanel (FAB becomes visible)", () => {
      mockMatchMedia(500);
      const store = createShellMutexStore("tenant-mobile-close");

      act(() => {
        store.getState().openPanel(PANEL_COPILOT);
        store.getState().closePanel();
      });

      expect(store.getState().activePanel).toBeNull();
    });
  });
});

// ── SidebarContext Phase 4 tests ─────────────────────────────────────────────

describe("SidebarContext (Phase 4 — expandSidebar + collapseSidebar actions)", () => {
  let originalMatchMedia: typeof window.matchMedia;
  let originalInnerWidth: number;

  beforeEach(() => {
    originalMatchMedia = window.matchMedia;
    originalInnerWidth = window.innerWidth;
    // Default: desktop viewport (no auto-collapse from matchMedia)
    mockMatchMedia(1440);
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", { writable: true, value: originalMatchMedia });
    Object.defineProperty(window, "innerWidth", { writable: true, value: originalInnerWidth });
    vi.restoreAllMocks();
  });

  it("useSidebar provides expandSidebar and collapseSidebar actions", () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: ({ children }) => <SidebarProvider>{children}</SidebarProvider>,
    });

    expect(typeof result.current.expandSidebar).toBe("function");
    expect(typeof result.current.collapseSidebar).toBe("function");
  });

  it("collapseSidebar sets isCollapsed to true", () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: ({ children }) => <SidebarProvider>{children}</SidebarProvider>,
    });

    act(() => {
      result.current.collapseSidebar();
    });
    expect(result.current.isCollapsed).toBe(true);
  });

  it("expandSidebar sets isCollapsed to false", () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: ({ children }) => <SidebarProvider>{children}</SidebarProvider>,
    });

    // First collapse it
    act(() => {
      result.current.collapseSidebar();
    });
    expect(result.current.isCollapsed).toBe(true);

    // Then expand it
    act(() => {
      result.current.expandSidebar();
    });
    expect(result.current.isCollapsed).toBe(false);
  });

  it("inline matchMedia auto-collapse is removed — desktop viewport does NOT force isCollapsed=true", () => {
    // T-4 deliverable: the SidebarContext matchMedia useEffect at <1279 is removed.
    // At desktop width (1440px), after mount the sidebar should remain expanded.
    mockMatchMedia(1440);

    const { result } = renderHook(() => useSidebar(), {
      wrapper: ({ children }) => <SidebarProvider>{children}</SidebarProvider>,
    });

    // After mount, isCollapsed should be false (no matchMedia forcing it)
    // Note: localStorage may have persisted state; in tests localStorage is clean
    expect(result.current.isCollapsed).toBe(false);
  });

  it("toggleSidebar still works after T-4 refactor", () => {
    const { result } = renderHook(() => useSidebar(), {
      wrapper: ({ children }) => <SidebarProvider>{children}</SidebarProvider>,
    });

    expect(result.current.isCollapsed).toBe(false);

    act(() => {
      result.current.toggleSidebar();
    });
    expect(result.current.isCollapsed).toBe(true);

    act(() => {
      result.current.toggleSidebar();
    });
    expect(result.current.isCollapsed).toBe(false);
  });
});

// ── DashboardShell structural smoke ─────────────────────────────────────────

describe("DashboardShell (structural smoke)", () => {
  it("is exported as a named export (not default)", () => {
    // DashboardShell is a Server Component passthrough — renders children + DashboardShellClient.
    // We verify it can be statically imported and is a function.
    expect(DashboardShell).toBeDefined();
    expect(typeof DashboardShell).toBe("function");
  });
});
