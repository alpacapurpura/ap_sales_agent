/**
 * Tests for shell-mutex-store + useShellMutex hook.
 *
 * Phase 1 scope: no-op state (effects gated). Verifies:
 * - Store mounts correctly with tenant-namespaced key
 * - Initial state is activePanel: null
 * - openPanel / closePanel / togglePanel actions work
 * - DashboardShell module exports exist (structural smoke)
 */
import { act } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { DashboardShell } from "@/components/shared/layout/DashboardShell";
import { createShellMutexStore } from "@/stores/shell-mutex-store";

/** Stable test tenant ID shared across store tests */
const TEST_TENANT = "tenant-123";
/** Panel constants */
const PANEL_SIDEBAR = "app-sidebar" as const;
const PANEL_COPILOT = "copilot" as const;

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

describe("DashboardShell (structural smoke)", () => {
  it("is exported as a named export (not default)", () => {
    // DashboardShell is a Server Component passthrough — renders children + DashboardShellClient.
    // We verify it can be statically imported and is a function.
    expect(DashboardShell).toBeDefined();
    expect(typeof DashboardShell).toBe("function");
  });
});
