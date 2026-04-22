import { renderHook } from "@testing-library/react";
import { describe, it, expect, beforeEach } from "vitest";

import { useCopilotStore } from "../../store/copilot-store";
import { useSuggestions } from "../use-suggestions";

describe("useSuggestions", () => {
  beforeEach(() => {
    useCopilotStore.setState({ currentRoute: null });
  });

  it("returns default suggestions when no route set", () => {
    const { result } = renderHook(() => useSuggestions());
    expect(result.current.chips.length).toBeGreaterThan(0);
    expect(result.current.isLoading).toBe(false);
  });

  it("returns brand-studio suggestions for brand-studio route", () => {
    useCopilotStore.setState({ currentRoute: "/tenant/brand-studio/identity" });
    const { result } = renderHook(() => useSuggestions());
    const ids = result.current.chips.map((c) => c.id);
    expect(ids.some((id) => id.startsWith("stub-brand"))).toBe(true);
  });

  it("returns offer-studio suggestions for offer route", () => {
    useCopilotStore.setState({ currentRoute: "/tenant/offer-studio" });
    const { result } = renderHook(() => useSuggestions());
    const ids = result.current.chips.map((c) => c.id);
    expect(ids.some((id) => id.startsWith("stub-offer"))).toBe(true);
  });

  it("returns growth-studio suggestions for growth route", () => {
    useCopilotStore.setState({ currentRoute: "/tenant/growth-studio" });
    const { result } = renderHook(() => useSuggestions());
    const ids = result.current.chips.map((c) => c.id);
    expect(ids.some((id) => id.startsWith("stub-growth"))).toBe(true);
  });

  it("each suggestion has label, prompt and id", () => {
    const { result } = renderHook(() => useSuggestions());
    result.current.chips.forEach((chip) => {
      expect(chip.id).toBeTruthy();
      expect(chip.label).toBeTruthy();
      expect(chip.prompt).toBeTruthy();
    });
  });

  it("falls back to default for unknown route", () => {
    useCopilotStore.setState({ currentRoute: "/tenant/unknown-module" });
    const { result } = renderHook(() => useSuggestions());
    const ids = result.current.chips.map((c) => c.id);
    expect(ids.some((id) => id.startsWith("stub-def"))).toBe(true);
  });
});
