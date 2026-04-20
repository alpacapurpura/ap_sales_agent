import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { useOnboardingWizard } from "../use-onboarding-wizard";

// Mock Next.js navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

describe("useOnboardingWizard", () => {
  it("starts at source-picker step", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    expect(result.current.currentStep).toBe("source-picker");
  });

  it("toggles source selection", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    expect(result.current.selectedSources).toContain("website");
    act(() => result.current.toggleSource("website"));
    expect(result.current.selectedSources).not.toContain("website");
  });

  it("routes to website step when website selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    act(() => result.current.next());
    expect(result.current.currentStep).toBe("website");
  });

  it("routes to documents step when only documents selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("documents"));
    act(() => result.current.next());
    expect(result.current.currentStep).toBe("documents");
  });

  it("routes to processing after last source step", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    act(() => result.current.next()); // → website
    act(() => result.current.next()); // → processing
    expect(result.current.currentStep).toBe("processing");
  });

  it("routes website → documents when both selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    act(() => result.current.toggleSource("documents"));
    act(() => result.current.next()); // → website
    act(() => result.current.next()); // → documents
    expect(result.current.currentStep).toBe("documents");
  });

  it("can go back", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    act(() => result.current.next()); // → website
    act(() => result.current.back()); // → source-picker
    expect(result.current.currentStep).toBe("source-picker");
  });

  it("computes step indices for progress bar", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("website"));
    act(() => result.current.toggleSource("documents"));
    // source-picker → website → documents → processing → gap-review
    expect(result.current.totalSteps).toBe(5);
    expect(result.current.currentStepIndex).toBe(0);
    act(() => result.current.next());
    expect(result.current.currentStepIndex).toBe(1);
  });

  it("manages files state", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    const file = new File(["content"], "test.pdf", { type: "application/pdf" });
    act(() => result.current.addFiles([file]));
    expect(result.current.files).toHaveLength(1);
    act(() => result.current.removeFile(0));
    expect(result.current.files).toHaveLength(0);
  });

  it("manages url state", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.setUrl("https://example.com"));
    expect(result.current.url).toBe("https://example.com");
  });

  it("navigates to interview page when only interview selected", () => {
    const { result } = renderHook(() => useOnboardingWizard());
    act(() => result.current.toggleSource("interview"));
    act(() => result.current.next());
    expect(mockPush).toHaveBeenCalledWith("/test-tenant/brand-studio/interview");
    // currentStep stays at source-picker (router.push was called instead)
    expect(result.current.currentStep).toBe("source-picker");
  });
});
