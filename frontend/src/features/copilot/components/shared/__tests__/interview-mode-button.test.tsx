import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

const {
  pushMock,
  mockStartInterview,
  mockSetSession,
  mockSetConversationId,
  mockAddMessage,
  mockSetSidebarState,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  mockStartInterview: vi.fn(),
  mockSetSession: vi.fn(),
  mockSetConversationId: vi.fn(),
  mockAddMessage: vi.fn(),
  mockSetSidebarState: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("@/features/copilot/api/interview-api", () => ({
  startInterview: (...args: unknown[]) => mockStartInterview(...args),
}));

vi.mock("@/features/copilot/store/copilot-store", () => {
  const state = {
    isOpen: false,
    setSession: mockSetSession,
    setConversationId: mockSetConversationId,
    addMessage: mockAddMessage,
    setSidebarState: mockSetSidebarState,
  };
  const useCopilotStore = (selector?: (s: typeof state) => unknown) =>
    selector ? selector(state) : state;
  useCopilotStore.getState = () => state;
  return { useCopilotStore };
});

import { InterviewModeButton } from "../InterviewModeButton";

describe("InterviewModeButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockStartInterview.mockResolvedValue({
      session_id: "sess-1",
      conversation_id: "conv-1",
      config: {},
      initial_message: "Hola",
    });
  });

  it("renders with default label", () => {
    render(<InterviewModeButton domain="brand" />);
    expect(screen.getByRole("button", { name: /modo entrevista/i })).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    render(<InterviewModeButton domain="brand" label="Iniciar entrevista" />);
    expect(screen.getByRole("button", { name: /iniciar entrevista/i })).toBeInTheDocument();
  });

  it("starts a brand interview and navigates to brand-studio", async () => {
    const user = userEvent.setup();
    render(<InterviewModeButton domain="brand" />);
    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(mockStartInterview).toHaveBeenCalledWith("test-token", "brand", undefined),
    );
    expect(mockSetSession).toHaveBeenCalled();
    expect(mockSetConversationId).toHaveBeenCalledWith("conv-1");
    expect(mockSetSidebarState).toHaveBeenCalledWith("open");
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio");
  });

  it("starts a buyer_persona interview with entityId and navigates to persona detail", async () => {
    const user = userEvent.setup();
    render(<InterviewModeButton domain="buyer_persona" entityId="persona-123" />);
    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(mockStartInterview).toHaveBeenCalledWith("test-token", "buyer_persona", "persona-123"),
    );
    expect(mockSetSession).toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio/publico/persona/persona-123");
  });

  it("without entityId navigates to the buyer-personas index (no interview)", async () => {
    const user = userEvent.setup();
    render(<InterviewModeButton domain="buyer_persona" />);
    await user.click(screen.getByRole("button"));

    expect(mockStartInterview).not.toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio/publico");
  });

  it("starts an offer interview with entityId and navigates to offer detail", async () => {
    const user = userEvent.setup();
    render(<InterviewModeButton domain="offer" entityId="offer-456" />);
    await user.click(screen.getByRole("button"));

    await waitFor(() =>
      expect(mockStartInterview).toHaveBeenCalledWith("test-token", "offer", "offer-456"),
    );
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/offer-studio/offer/offer-456");
  });

  it("without entityId navigates to the offer-studio index (no interview)", async () => {
    const user = userEvent.setup();
    render(<InterviewModeButton domain="offer" />);
    await user.click(screen.getByRole("button"));

    expect(mockStartInterview).not.toHaveBeenCalled();
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/offer-studio");
  });

  it("still navigates when interview start fails", async () => {
    const user = userEvent.setup();
    mockStartInterview.mockRejectedValue(new Error("boom"));
    render(<InterviewModeButton domain="brand" />);
    await user.click(screen.getByRole("button"));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio"));
  });

  it("renders a sparkle icon by default", () => {
    render(<InterviewModeButton domain="brand" />);
    const button = screen.getByRole("button");
    expect(button.querySelector("svg")).toBeTruthy();
  });

  it("applies additional className", () => {
    render(<InterviewModeButton domain="brand" className="extra-class" />);
    expect(screen.getByRole("button").className).toContain("extra-class");
  });
});
