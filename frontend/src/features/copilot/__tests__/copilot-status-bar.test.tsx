import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    data: {
      session_id: "session-123",
      domain: "offer",
      domain_label: "Oferta",
      bloques_completados: ["intro", "strategy"],
      total_bloques: 6,
    },
  }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token") }),
}));

import { CopilotStatusBar } from "../components/CopilotStatusBar";
import { useCopilotStore } from "../store/copilot-store";

describe("CopilotStatusBar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      interviewSessionId: null,
      focusEntity: null,
      sidebarState: "collapsed",
      isOpen: false,
    });
  });

  it("shows Continuar button when paused interview exists", () => {
    render(<CopilotStatusBar />);
    expect(screen.getByText(/Continuar/)).toBeDefined();
  });

  it("restores interview on continue click", async () => {
    const user = userEvent.setup();
    render(<CopilotStatusBar />);
    await user.click(screen.getByText(/Continuar/));
    const state = useCopilotStore.getState();
    expect(state.interviewSessionId).toBe("session-123");
    expect(state.sidebarState).toBe("expanded");
  });

  it("is NOT hardcoded to /brand-studio/interview", () => {
    const { container } = render(<CopilotStatusBar />);
    expect(container.innerHTML).not.toContain("/brand-studio/interview");
  });

  it("hides when interview already active in sidebar", () => {
    useCopilotStore.setState({ interviewSessionId: "already-active" });
    const { container } = render(<CopilotStatusBar />);
    expect(container.innerHTML).toBe("");
  });
});
