import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { useCopilotStore } from "../store/copilot-store";
import { FocusModeButton } from "../components/focus-mode-button";

describe("FocusModeButton", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      sidebarState: "collapsed",
      isOpen: false,
      focusEntity: null,
      focusSnapshot: null,
      selectedFields: [],
    });
  });

  it("activates focus and expands sidebar on click", async () => {
    const user = userEvent.setup();
    render(
      <FocusModeButton
        domain="offer"
        entityId="abc-123"
        label="Oferta Premium"
        entityData={{ public_name: "Oferta Premium" }}
      />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity).toEqual({
      domain: "offer",
      entityId: "abc-123",
      label: "Oferta Premium",
    });
    expect(state.focusSnapshot).toEqual({ public_name: "Oferta Premium" });
    expect(state.sidebarState).toBe("expanded");
  });

  it("clears selected fields when activating focus", async () => {
    const user = userEvent.setup();
    useCopilotStore.setState({
      selectedFields: [
        { fieldId: "field-1", fieldLabel: "Label 1", fieldValue: "Value 1" },
      ],
    });

    render(
      <FocusModeButton
        domain="brand"
        label="Mi Marca"
        entityData={{ name: "Brand" }}
      />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.selectedFields).toHaveLength(0);
  });

  it("renders Focus text", () => {
    render(
      <FocusModeButton
        domain="brand"
        label="Mi Marca"
        entityData={{}}
      />,
    );
    expect(screen.getByText("Focus")).toBeDefined();
  });

  it("accepts optional entityId", async () => {
    const user = userEvent.setup();
    render(
      <FocusModeButton
        domain="buyer_persona"
        entityId="persona-xyz"
        label="Executive"
        entityData={{ title: "C-suite" }}
      />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity?.entityId).toBe("persona-xyz");
  });

  it("works without entityId", async () => {
    const user = userEvent.setup();
    render(
      <FocusModeButton
        domain="brand"
        label="Generic Brand"
        entityData={{ name: "Generic" }}
      />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity?.entityId).toBeUndefined();
    expect(state.focusEntity?.label).toBe("Generic Brand");
  });

  it("applies custom className", () => {
    const { container } = render(
      <FocusModeButton
        domain="brand"
        label="Test"
        entityData={{}}
        className="custom-class"
      />,
    );

    const button = container.querySelector("button");
    expect(button?.className).toContain("custom-class");
  });
});
