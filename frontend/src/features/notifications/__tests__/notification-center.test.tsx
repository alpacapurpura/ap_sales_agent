import { render } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";

import { useCopilotStore } from "@/features/copilot/store/copilot-store";

import { NotificationCenter } from "../components/NotificationCenter";
import { useDismissStore } from "../store/dismiss-store";

/**
 * The "paused interview" notification category was retired with the
 * standalone interview engine (2026-04-22). The aggregator currently yields
 * no notifications; this suite only verifies the centre renders empty
 * without throwing until a guided-in-progress notification is introduced.
 */
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

  it("renders without crashing when there are no notifications", () => {
    const { container } = render(<NotificationCenter />);
    expect(container).toBeDefined();
    // No pill should be surfaced while the notifications pipeline is empty.
    expect(container.querySelector("button[aria-label*='Avisos']")).toBeNull();
  });
});
