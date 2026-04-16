import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { FocusBar } from "../components/FocusBar";
import { useCopilotStore } from "../store/copilot-store";

describe("FocusBar", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Oferta Premium" },
      focusSnapshot: { public_name: "Original" },
      interviewSessionId: null,
      interviewProgress: null,
      sidebarState: "expanded",
      isOpen: true,
    });
  });

  it("shows entity label", () => {
    render(<FocusBar />);
    expect(screen.getByText("Oferta Premium")).toBeDefined();
  });

  it("shows exit focus button", () => {
    render(<FocusBar />);
    expect(screen.getByText("Salir de Focus")).toBeDefined();
  });

  it("clears focus and sets sidebar to open on exit", async () => {
    const user = userEvent.setup();
    render(<FocusBar />);
    await user.click(screen.getByText("Salir de Focus"));
    const state = useCopilotStore.getState();
    expect(state.focusEntity).toBeNull();
    expect(state.sidebarState).toBe("open");
  });

  it("shows progress dots in interview mode", () => {
    useCopilotStore.setState({
      interviewSessionId: "session-1",
      interviewProgress: { currentBlock: "strategy", blocksCompleted: ["intro"], totalBlocks: 5 },
    });
    render(<FocusBar />);
    const dots = document.querySelectorAll("[data-testid='progress-dot']");
    expect(dots.length).toBe(5);
  });

  it("renders nothing when no focusEntity", () => {
    useCopilotStore.setState({ focusEntity: null });
    const { container } = render(<FocusBar />);
    expect(container.innerHTML).toBe("");
  });
});
