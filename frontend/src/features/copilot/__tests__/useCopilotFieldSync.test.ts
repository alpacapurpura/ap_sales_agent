import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useCopilotFieldSync } from "@/features/copilot/hooks/useCopilotFieldSync";

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useCopilotFieldSync", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("registers a copilot:field-update event listener on mount", () => {
    const addSpy = vi.spyOn(window, "addEventListener");
    const setValue = vi.fn();

    renderHook(() => useCopilotFieldSync(setValue));

    expect(addSpy).toHaveBeenCalledWith("copilot:field-update", expect.any(Function));
  });

  it("removes the event listener on unmount", () => {
    const removeSpy = vi.spyOn(window, "removeEventListener");
    const setValue = vi.fn();

    const { unmount } = renderHook(() => useCopilotFieldSync(setValue));
    unmount();

    expect(removeSpy).toHaveBeenCalledWith("copilot:field-update", expect.any(Function));
  });

  it("calls setValue with field_id directly when no fieldMap is provided", () => {
    const setValue = vi.fn();
    renderHook(() => useCopilotFieldSync(setValue));

    const event = new CustomEvent("copilot:field-update", {
      detail: { fieldId: "brand_name", newValue: "Acme Corp" },
    });
    window.dispatchEvent(event);

    expect(setValue).toHaveBeenCalledWith("brand_name", "Acme Corp", {
      shouldDirty: true,
      shouldValidate: true,
    });
  });

  it("maps field_id through fieldMap when provided", () => {
    const setValue = vi.fn();
    const fieldMap = { uvp: "positioning.uvp", brand_name: "identity.brand_name" };
    renderHook(() => useCopilotFieldSync(setValue, fieldMap));

    const event = new CustomEvent("copilot:field-update", {
      detail: { fieldId: "uvp", newValue: "The best solution" },
    });
    window.dispatchEvent(event);

    expect(setValue).toHaveBeenCalledWith("positioning.uvp", "The best solution", {
      shouldDirty: true,
      shouldValidate: true,
    });
  });

  it("falls back to field_id when fieldMap does not contain the incoming id", () => {
    const setValue = vi.fn();
    const fieldMap = { uvp: "positioning.uvp" };
    renderHook(() => useCopilotFieldSync(setValue, fieldMap));

    const event = new CustomEvent("copilot:field-update", {
      detail: { fieldId: "unknown_field", newValue: "some value" },
    });
    window.dispatchEvent(event);

    expect(setValue).toHaveBeenCalledWith("unknown_field", "some value", {
      shouldDirty: true,
      shouldValidate: true,
    });
  });
});
