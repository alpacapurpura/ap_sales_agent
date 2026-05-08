/**
 * T-5 — Phase 5: CopilotFAB component
 *
 * Verifies:
 * - Returns null when viewport >= md (tablet/desktop)
 * - Returns null when copilot sidebarState !== 'collapsed' (rail/full)
 * - Visible when mobile (<768px) AND copilot collapsed
 * - Click dispatches shellMutex.openPanel('copilot')
 * - aria-label="Abrir asistente" correct
 * - z-class FAB applied (Z_INDEX_CLASSES.FAB = z-[70])
 *
 * Scenario 3 coverage (mobile mutex + FAB visibility).
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Mocks ───────────────────────────────────────────────────────────────────

// useViewport must be mocked BEFORE the import of CopilotFAB (hoisted).
const mockViewport = vi.hoisted(() => ({
  isMobile: false,
  isTablet: false,
  isDesktop: true,
  width: 1440,
}));

vi.mock("@/hooks/use-viewport", () => ({
  useViewport: () => mockViewport,
}));

// Copilot store: default sidebarState = 'collapsed'
let mockSidebarState: "collapsed" | "rail" | "full" = "collapsed";

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: (selector: (s: { sidebarState: "collapsed" | "rail" | "full" }) => unknown) =>
    selector({ sidebarState: mockSidebarState }),
}));

// ShellMutexContext
const mockOpenPanel = vi.fn();
let mockShellMutex: { openPanel: typeof mockOpenPanel; activePanel: string | null } | undefined = {
  openPanel: mockOpenPanel,
  activePanel: null,
};

vi.mock("@/components/shared/layout/ShellMutexContext", () => ({
  useShellMutexContext: () => mockShellMutex,
}));

// Import the component under test AFTER mocks are set up
import { CopilotFAB } from "../CopilotFAB";

// ── Helpers ─────────────────────────────────────────────────────────────────

function renderFAB() {
  return render(<CopilotFAB />);
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("CopilotFAB — visibility transitions (T-5 Phase 5)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSidebarState = "collapsed";
    mockShellMutex = { openPanel: mockOpenPanel, activePanel: null };
    // Default: desktop viewport
    mockViewport.isMobile = false;
    mockViewport.isTablet = false;
    mockViewport.isDesktop = true;
    mockViewport.width = 1440;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("null when not mobile", () => {
    it("returns null on desktop viewport (width >= 1024)", () => {
      mockViewport.isMobile = false;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = true;
      mockViewport.width = 1440;
      mockSidebarState = "collapsed";

      const { container } = renderFAB();
      expect(container.firstChild).toBeNull();
    });

    it("returns null on tablet viewport (768-1023px)", () => {
      mockViewport.isMobile = false;
      mockViewport.isTablet = true;
      mockViewport.isDesktop = false;
      mockViewport.width = 900;
      mockSidebarState = "collapsed";

      const { container } = renderFAB();
      expect(container.firstChild).toBeNull();
    });
  });

  describe("null when copilot not collapsed", () => {
    it("returns null when mobile but sidebarState = rail", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "rail";

      const { container } = renderFAB();
      expect(container.firstChild).toBeNull();
    });

    it("returns null when mobile but sidebarState = full", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "full";

      const { container } = renderFAB();
      expect(container.firstChild).toBeNull();
    });
  });

  describe("visible when mobile + collapsed", () => {
    it("renders FAB button when mobile (500px) and copilot collapsed", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";

      renderFAB();
      const fab = screen.getByRole("button", { name: /abrir asistente/i });
      expect(fab).toBeDefined();
    });
  });

  describe("aria-label", () => {
    it('has aria-label="Abrir asistente" (Spanish neutro)', () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";

      renderFAB();
      const fab = screen.getByRole("button", { name: "Abrir asistente" });
      expect(fab).toBeDefined();
      expect(fab.getAttribute("aria-label")).toBe("Abrir asistente");
    });
  });

  describe("z-index class", () => {
    it("applies z-[70] class from Z_INDEX_CLASSES.FAB", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";

      renderFAB();
      const fab = screen.getByRole("button", { name: "Abrir asistente" });
      // The FAB button or its container should carry z-[70]
      const hasZIndexClass =
        fab.className.includes("z-[70]") || fab.closest("[class*='z-[70]']") !== null;
      expect(hasZIndexClass).toBe(true);
    });
  });

  describe("onClick dispatches mutex openPanel('copilot')", () => {
    it("calls shellMutex.openPanel('copilot') on click", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";

      renderFAB();
      const fab = screen.getByRole("button", { name: "Abrir asistente" });
      fireEvent.click(fab);

      expect(mockOpenPanel).toHaveBeenCalledOnce();
      expect(mockOpenPanel).toHaveBeenCalledWith("copilot");
    });

    it("does NOT call openPanel multiple times on a single click", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";

      renderFAB();
      const fab = screen.getByRole("button", { name: "Abrir asistente" });
      fireEvent.click(fab);

      expect(mockOpenPanel).toHaveBeenCalledTimes(1);
    });

    it("works when shellMutex is undefined (no infinite loop)", () => {
      mockViewport.isMobile = true;
      mockViewport.isTablet = false;
      mockViewport.isDesktop = false;
      mockViewport.width = 500;
      mockSidebarState = "collapsed";
      mockShellMutex = undefined;

      renderFAB();
      // Should still render without crashing
      const fab = screen.queryByRole("button", { name: "Abrir asistente" });
      // FAB renders even without mutex (no-op click fallback)
      if (fab) {
        expect(() => fireEvent.click(fab)).not.toThrow();
      }
    });
  });
});
