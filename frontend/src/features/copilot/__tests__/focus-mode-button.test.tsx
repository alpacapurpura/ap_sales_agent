import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach, vi } from "vitest";

import { FocusModeButton } from "../components/focus-mode-button";
import { useCopilotStore } from "../store/copilot-store";

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
      selectedFields: [{ fieldId: "field-1", fieldLabel: "Label 1", fieldValue: "Value 1" }],
    });

    render(<FocusModeButton domain="brand" label="Mi Marca" entityData={{ name: "Brand" }} />);

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.selectedFields).toHaveLength(0);
  });

  it("renders Focus text", () => {
    render(<FocusModeButton domain="brand" label="Mi Marca" entityData={{}} />);
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
      <FocusModeButton domain="brand" label="Generic Brand" entityData={{ name: "Generic" }} />,
    );

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusEntity?.entityId).toBeUndefined();
    expect(state.focusEntity?.label).toBe("Generic Brand");
  });

  it("applies custom className", () => {
    const { container } = render(
      <FocusModeButton domain="brand" label="Test" entityData={{}} className="custom-class" />,
    );

    const button = container.querySelector("button");
    expect(button?.className).toContain("custom-class");
  });

  // ── R3: Fresh data at activation time ────────────────────────────────

  it("uses getEntityData() result instead of stale entityData prop on click", async () => {
    const user = userEvent.setup();
    const staleData = { name: "Old Name" };
    const freshData = { name: "Fresh Name", updated: true };
    const getEntityData = vi.fn(() => freshData);

    render(
      <FocusModeButton
        domain="brand"
        label="Mi Marca"
        entityData={staleData}
        getEntityData={getEntityData}
      />,
    );

    await user.click(screen.getByRole("button"));

    expect(getEntityData).toHaveBeenCalledOnce();
    const state = useCopilotStore.getState();
    expect(state.focusSnapshot).toEqual(freshData);
    expect(state.focusSnapshot).not.toEqual(staleData);
  });

  it("falls back to entityData prop when getEntityData is not provided", async () => {
    const user = userEvent.setup();
    const entityData = { name: "Static" };

    render(<FocusModeButton domain="brand" label="Mi Marca" entityData={entityData} />);

    await user.click(screen.getByRole("button"));

    const state = useCopilotStore.getState();
    expect(state.focusSnapshot).toEqual(entityData);
  });

  // ── UX3: Prefetch on hover ───────────────────────────────────────────

  it("calls prefetchFn on mouse enter", async () => {
    const user = userEvent.setup();
    const prefetchFn = vi.fn();

    render(
      <FocusModeButton
        domain="offer"
        entityId="offer-1"
        label="Test Offer"
        entityData={{}}
        prefetchFn={prefetchFn}
      />,
    );

    await user.hover(screen.getByRole("button"));

    expect(prefetchFn).toHaveBeenCalledOnce();
  });

  it("does not throw when prefetchFn is not provided and hovering", async () => {
    const user = userEvent.setup();

    render(<FocusModeButton domain="brand" label="No Prefetch" entityData={{}} />);

    // Should not throw
    await expect(user.hover(screen.getByRole("button"))).resolves.toBeUndefined();
  });

  it("prefetchFn is called only once per hover entry", async () => {
    const user = userEvent.setup();
    const prefetchFn = vi.fn();

    render(
      <FocusModeButton
        domain="offer"
        entityId="offer-2"
        label="Test"
        entityData={{}}
        prefetchFn={prefetchFn}
      />,
    );

    const button = screen.getByRole("button");
    await user.hover(button);
    await user.unhover(button);
    await user.hover(button);

    // Called each time mouse enters
    expect(prefetchFn).toHaveBeenCalledTimes(2);
  });
});
