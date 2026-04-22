import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render as rtlRender, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

/** Wrap render() with a fresh QueryClientProvider so React Query hooks resolve. */
function render(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return rtlRender(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token") }),
}));

vi.mock("../hooks/use-voice-recorder", () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isTranscribing: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    cancelRecording: vi.fn(),
    error: null,
    duration: 0,
  }),
}));

vi.mock("../hooks/use-proactive-nudges", () => ({
  useProactiveNudges: () => ({ nudges: [], dismissNudge: vi.fn() }),
}));

vi.mock("../api/copilot-api", () => ({
  streamCopilotChat: vi.fn(),
  reportCopilotEvent: vi.fn(),
}));

vi.mock("../hooks/use-copilot-navigator", () => ({
  useCopilotNavigator: () => ({ executeAction: vi.fn() }),
}));

import { CopilotSidebar } from "../components/CopilotSidebar";
import { useCopilotStore } from "../store/copilot-store";

describe("CopilotSidebar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: "collapsed",
      isOpen: false,
      messages: [],
      status: "idle",
      conversationId: null,
      session: null,
      focusedField: null,
      currentRoute: null,
      pendingUIActions: [],
      selectedFields: [],
      activeProcedure: null,
    });
  });

  it("renders the sidebar container when collapsed", () => {
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside).not.toBeNull();
    // Collapsed: grid-template-columns with rail-only width.
    const style = aside?.getAttribute("style") ?? "";
    expect(style.length).toBeGreaterThan(0);
  });

  it("renders chat panel when expanded to rail state", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside).not.toBeNull();
    // Rail state: grid-template-columns lists a non-zero chat width before the 60px rail.
    const style = aside?.getAttribute("style") ?? "";
    expect(style).toMatch(/grid-template-columns/i);
    expect(style).toMatch(/60px/);
  });

  it("header surfaces session label when a session is active", () => {
    useCopilotStore.setState({
      sidebarState: "rail",
      isOpen: true,
      session: {
        sectionKey: "offer.pricing",
        label: "Oferta Premium",
        entityId: "123",
        procedure: "free",
        sessionId: null,
        startedAt: new Date(),
        snapshot: {},
      },
    });
    render(<CopilotSidebar />);
    expect(screen.getByText(/Oferta Premium/)).toBeDefined();
  });

  it("header shows generic Chat label when no session is active", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    render(<CopilotSidebar />);
    expect(screen.getByText("Chat")).toBeDefined();
  });
});
