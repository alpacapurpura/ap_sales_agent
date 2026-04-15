import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useCopilotStore } from "../../store/copilot-store";
import { WithCopilot } from "../WithCopilot";

// Mock lucide-react icons to avoid SVG rendering issues in tests
vi.mock("lucide-react", () => ({
  Plus: () => null,
  Check: () => null,
}));

describe("WithCopilot AI badge", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      selectedFields: [],
      focusEntity: null,
    });
  });

  it("shows IA badge when field updated via copilot in focus mode", () => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
    });

    render(
      <WithCopilot fieldId="headline" fieldLabel="Headline" getValue={() => "val"}>
        <input />
      </WithCopilot>,
    );

    act(() => {
      window.dispatchEvent(
        new CustomEvent("copilot:field-update", {
          detail: { fieldId: "headline", newValue: "AI value" },
        }),
      );
    });

    expect(screen.getByText("IA")).toBeTruthy();
  });

  it("does NOT show IA badge when not in focus mode", () => {
    render(
      <WithCopilot fieldId="headline" fieldLabel="Headline" getValue={() => "val"}>
        <input />
      </WithCopilot>,
    );

    act(() => {
      window.dispatchEvent(
        new CustomEvent("copilot:field-update", {
          detail: { fieldId: "headline", newValue: "AI value" },
        }),
      );
    });

    expect(screen.queryByText("IA")).toBeNull();
  });
});
