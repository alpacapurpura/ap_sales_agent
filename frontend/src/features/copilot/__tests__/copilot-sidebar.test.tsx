import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token") }),
}));

vi.mock("../hooks/useVoiceRecorder", () => ({
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

vi.mock("../hooks/useProactiveNudges", () => ({
  useProactiveNudges: () => ({ nudges: [], dismissNudge: vi.fn() }),
}));

vi.mock("../api/copilot-api", () => ({
  streamCopilotChat: vi.fn(),
  reportCopilotEvent: vi.fn(),
}));

vi.mock("../hooks/useCopilotNavigator", () => ({
  useCopilotNavigator: () => ({ executeAction: vi.fn() }),
}));

import { useCopilotStore } from "../store/copilot-store";
import { CopilotSidebar } from "../components/copilot-sidebar";

describe("CopilotSidebar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: "collapsed",
      isOpen: false,
      messages: [],
      status: "idle",
      conversationId: null,
      focusEntity: null,
      focusSnapshot: null,
      interviewSessionId: null,
      interviewProgress: null,
      previewData: null,
      interviewPreviewData: null,
      currentRoute: null,
      pendingUIActions: [],
      selectedFields: [],
      activeProcedure: null,
      interviewMode: false,
    });
  });

  it("renders rail when collapsed", () => {
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[60px]");
  });

  it("renders chat panel when open", () => {
    useCopilotStore.setState({ sidebarState: "open", isOpen: true });
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[380px]");
  });

  it("renders expanded width when expanded", () => {
    useCopilotStore.setState({
      sidebarState: "expanded",
      isOpen: true,
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
    });
    render(<CopilotSidebar />);
    const aside = document.querySelector("aside");
    expect(aside?.className).toContain("w-[780px]");
  });

  it("shows mode indicator in header — Focus", () => {
    useCopilotStore.setState({
      sidebarState: "open",
      isOpen: true,
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
    });
    render(<CopilotSidebar />);
    expect(screen.getByText(/Focus: Oferta Premium/)).toBeDefined();
  });

  it("shows Chat label when no focus", () => {
    useCopilotStore.setState({ sidebarState: "open", isOpen: true });
    render(<CopilotSidebar />);
    expect(screen.getByText("Chat")).toBeDefined();
  });
});
