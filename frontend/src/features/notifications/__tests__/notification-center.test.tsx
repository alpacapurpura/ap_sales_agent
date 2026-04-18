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

import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import { NotificationCenter } from "../components/NotificationCenter";
import { useDismissStore } from "../store/dismiss-store";

describe("NotificationCenter", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      session: null,
      focusedField: null,
      sidebarState: "collapsed",
      isOpen: false,
    });
    useDismissStore.setState({ dismissedIds: {} });
  });

  it("shows floating pill with count when paused interview exists", () => {
    render(<NotificationCenter />);
    expect(screen.getByLabelText(/Avisos \(1\)/)).toBeDefined();
  });

  it("opens panel with Continuar CTA on pill click", async () => {
    const user = userEvent.setup();
    render(<NotificationCenter />);
    await user.click(screen.getByLabelText(/Avisos \(1\)/));
    expect(screen.getByText(/Continuar/)).toBeDefined();
  });

  it("restores interview as a session when Continuar is clicked", async () => {
    const user = userEvent.setup();
    render(<NotificationCenter />);
    await user.click(screen.getByLabelText(/Avisos \(1\)/));
    await user.click(screen.getByText(/Continuar/));
    const state = useCopilotStore.getState();
    expect(state.session?.sessionId).toBe("session-123");
    expect(state.session?.procedure).toBe("interview");
    expect(state.sidebarState).toBe("open");
  });

  it("hides when a session is already active", () => {
    useCopilotStore.setState({
      session: {
        sectionKey: "offer.root",
        label: "Oferta",
        entityId: null,
        procedure: "interview",
        sessionId: "already-active",
        startedAt: new Date(),
        snapshot: {},
      },
    });
    const { container } = render(<NotificationCenter />);
    expect(container.innerHTML).toBe("");
  });

  it("hides pill after dismiss", () => {
    useDismissStore.getState().dismiss("interview-session-123");
    const { container } = render(<NotificationCenter />);
    expect(container.innerHTML).toBe("");
  });
});
