/**
 * T-2 Scenario 2 — CopilotSidebar grid template columns consume COPILOT_WIDTHS SSoT.
 *
 * Validates that the CSS grid `gridTemplateColumns` attribute in CopilotSidebar
 * matches the SSoT constants for each sidebarState:
 *  - collapsed: `0px 60px` (no chat panel, 60px rail)
 *  - rail:      `400px 60px` (chat panel, rail)
 *  - full:      `400px 280px` (chat panel, history panel — no separate rail)
 */
import { render } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { COPILOT_WIDTHS } from "@/features/copilot/lib/copilot-shell-widths";

// ── Mocks ────────────────────────────────────────────────────────────

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: vi.fn(),
  loadPersistedSidebarState: vi.fn(() => "collapsed"),
}));

vi.mock("@/features/copilot/hooks/use-copilot-navigator", () => ({
  useCopilotNavigator: vi.fn(),
}));
vi.mock("@/features/copilot/hooks/use-create-conversation", () => ({
  useCreateConversation: vi.fn(() => ({ mutate: vi.fn() })),
}));
vi.mock("@/features/copilot/hooks/use-route-tracker", () => ({
  useRouteTracker: vi.fn(),
}));
vi.mock("@/features/copilot/components/CopilotChatPanel", () => ({
  CopilotChatPanel: () => <div data-testid="chat-panel" />,
}));
vi.mock("@/features/copilot/components/CopilotHistoryPanel", () => ({
  CopilotHistoryPanel: () => <div data-testid="history-panel" />,
}));
vi.mock("@/features/copilot/components/CopilotRail", () => ({
  CopilotRail: () => <div data-testid="rail-panel" />,
}));

import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { CopilotSidebar } from "@/features/copilot/components/CopilotSidebar";
import type { SidebarState } from "@/features/copilot/store/copilot-store";

const mockUseCopilotStore = vi.mocked(useCopilotStore);

function mockStore(sidebarState: SidebarState) {
  mockUseCopilotStore.mockImplementation((selector) => {
    const fakeStore = {
      sidebarState,
      setSidebarState: vi.fn(),
      cycleSidebarState: vi.fn(),
    };
    return selector(fakeStore as unknown as Parameters<typeof selector>[0]);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("CopilotSidebar grid-template-columns === COPILOT_WIDTHS SSoT", () => {
  it("collapsed state: grid columns = '0px 60px' (chat=0, rail=60)", () => {
    mockStore("collapsed");
    const { getByTestId } = render(<CopilotSidebar />);
    const aside = getByTestId("copilot-sidebar");

    const expected = `${0}px ${COPILOT_WIDTHS.collapsed}px`;
    expect(aside.style.gridTemplateColumns).toBe(expected);
    expect(aside.style.gridTemplateColumns).toBe("0px 60px");
  });

  it("rail state: grid columns = '400px 60px' (chat=400, rail=60)", () => {
    mockStore("rail");
    const { getByTestId } = render(<CopilotSidebar />);
    const aside = getByTestId("copilot-sidebar");

    const expected = `${COPILOT_WIDTHS.chat}px ${COPILOT_WIDTHS.collapsed}px`;
    expect(aside.style.gridTemplateColumns).toBe(expected);
    expect(aside.style.gridTemplateColumns).toBe("400px 60px");
  });

  it("full state: grid columns = '400px 280px' (chat=400, history=280)", () => {
    mockStore("full");
    const { getByTestId } = render(<CopilotSidebar />);
    const aside = getByTestId("copilot-sidebar");

    const expected = `${COPILOT_WIDTHS.chat}px ${COPILOT_WIDTHS.rail}px`;
    expect(aside.style.gridTemplateColumns).toBe(expected);
    expect(aside.style.gridTemplateColumns).toBe("400px 280px");
  });
});
