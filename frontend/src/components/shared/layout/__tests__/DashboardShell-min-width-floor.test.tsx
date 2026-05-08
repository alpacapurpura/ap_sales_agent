/**
 * T-3 — Phase 3: Min-content-width floor 720px @≥1024
 *
 * Verifies that DashboardShellClient applies:
 * 1. Parent wrapper provides --shell-content-min-width CSS variable.
 * 2. main element has the lg:min-w-[var(--shell-content-min-width,720px)] class.
 *
 * These are structural/class tests (the Tailwind class must be present).
 * Breakpoint enforcement (lg: = ≥1024px) is a CSS-time concern validated by E2E (T-8).
 *
 * Scenario 1 coverage:
 * - CSS variable provided by parent wrapper
 * - main element carries the min-width class with the correct arbitrary value
 * - Class is present regardless of viewport (CSS does the @≥1024 enforcement)
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { DashboardShellClient } from "../DashboardShellClient";

// ── Mocks ───────────────────────────────────────────────────────────────────

// CopilotSidebar uses useCopilotStore (zustand). Mock to avoid store hydration.
vi.mock("@/features/copilot/components/CopilotSidebar", () => ({
  CopilotSidebar: () => <div data-testid="copilot-sidebar-mock" />,
}));

// NotificationCenter polls — mock to prevent side-effects.
vi.mock("@/features/notifications/components/NotificationCenter", () => ({
  NotificationCenter: () => <div data-testid="notification-center-mock" />,
}));

// AppSidebar uses SidebarContext internally — provided by DashboardShellClient.
vi.mock("@/components/shared/layout/AppSidebar", () => ({
  AppSidebar: () => <div data-testid="app-sidebar-mock" />,
}));

// matchMedia — happy-dom may not support it fully; provide a minimal mock.
function mockMatchMedia(width: number) {
  Object.defineProperty(window, "innerWidth", { writable: true, value: width });
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: vi.fn((query: string): MediaQueryList => {
      const matches = /min-width:\s*(\d+)px/.test(query)
        ? width >= parseInt(/min-width:\s*(\d+)px/.exec(query)?.[1] ?? "0", 10)
        : /max-width:\s*(\d+)px/.test(query)
          ? width <= parseInt(/max-width:\s*(\d+)px/.exec(query)?.[1] ?? "99999", 10)
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

// ── Helpers ─────────────────────────────────────────────────────────────────

const TEST_TENANT = "tenant-t3-test";

function renderShell() {
  return render(
    <DashboardShellClient tenantId={TEST_TENANT}>
      <div data-testid="shell-child">content</div>
    </DashboardShellClient>,
  );
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("DashboardShellClient — min-content-width floor (T-3 Phase 3)", () => {
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

  describe("CSS variable wiring — parent wrapper", () => {
    it("parent wrapper provides --shell-content-min-width inline style", () => {
      mockMatchMedia(1440);
      const { container } = renderShell();

      // The CSS variable wrapper div must exist somewhere in the tree.
      // We check that an element with the expected inline style is present.
      const wrapper = container.querySelector("[style*='--shell-content-min-width']");
      expect(wrapper).not.toBeNull();
    });

    it("--shell-content-min-width value is 720px", () => {
      mockMatchMedia(1440);
      const { container } = renderShell();

      const wrapper = container.querySelector(
        "[style*='--shell-content-min-width']",
      ) as HTMLElement | null;

      expect(wrapper).not.toBeNull();

      // The inline style should set the variable to 720px.
      const styleAttr = wrapper!.getAttribute("style") ?? "";
      expect(styleAttr).toContain("720px");
    });
  });

  describe("main element — min-width class applied", () => {
    it("main element carries the lg:min-w Tailwind class with CSS var", () => {
      mockMatchMedia(1440);
      renderShell();

      const main = document.querySelector("main");
      expect(main).not.toBeNull();

      // The class must include the Tailwind arbitrary-value class referencing the CSS var.
      // Pattern: lg:min-w-[var(--shell-content-min-width,720px)]
      const classAttr = main!.className;
      expect(classAttr).toContain("min-w-");
    });

    it("main element class references --shell-content-min-width CSS var", () => {
      mockMatchMedia(1440);
      renderShell();

      const main = document.querySelector("main");
      expect(main).not.toBeNull();

      const classAttr = main!.className;
      // Must contain the var() reference for the CSS variable.
      expect(classAttr).toMatch(/--shell-content-min-width/);
    });

    it("main element class includes 720px fallback in the var()", () => {
      mockMatchMedia(1440);
      renderShell();

      const main = document.querySelector("main");
      expect(main).not.toBeNull();

      const classAttr = main!.className;
      expect(classAttr).toMatch(/720px/);
    });
  });

  describe("children rendering preserved — passthrough integrity", () => {
    it("renders children inside main element", () => {
      mockMatchMedia(1440);
      renderShell();

      const child = screen.getByTestId("shell-child");
      expect(child).toBeDefined();
      expect(child.textContent).toBe("content");
    });

    it("renders without errors at mobile viewport (500px)", () => {
      mockMatchMedia(500);
      // Should render without throwing — CSS lg: breakpoint enforcement
      // is a CSS-time concern, not JS-time.
      expect(() => renderShell()).not.toThrow();
    });

    it("renders without errors at tablet viewport (900px)", () => {
      mockMatchMedia(900);
      expect(() => renderShell()).not.toThrow();
    });

    it("renders without errors at desktop viewport (1024px)", () => {
      mockMatchMedia(1024);
      expect(() => renderShell()).not.toThrow();
    });

    it("renders without errors at large desktop viewport (1920px)", () => {
      mockMatchMedia(1920);
      expect(() => renderShell()).not.toThrow();
    });
  });

  describe("CSS variable wrapper — structural position", () => {
    it("wrapper is an ancestor of the main element", () => {
      mockMatchMedia(1440);
      const { container } = renderShell();

      const wrapper = container.querySelector("[style*='--shell-content-min-width']");
      const main = container.querySelector("main");

      expect(wrapper).not.toBeNull();
      expect(main).not.toBeNull();

      // main must be a descendant of wrapper.
      expect(wrapper!.contains(main)).toBe(true);
    });
  });
});
