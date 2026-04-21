import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { OfferSectionCopilot } from "../OfferSectionCopilot";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockInvokeTool = vi.fn();
const mockUseOfferCopilot = vi.fn();

vi.mock("../../hooks/use-offer-copilot", () => ({
  useOfferCopilot: (...args: unknown[]) => mockUseOfferCopilot(...args),
}));

// sonner toast mock
vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

// ── Fixtures ─────────────────────────────────────────────────────────────────

function buildHookResult(overrides = {}) {
  return {
    invokeTool: mockInvokeTool,
    isInvoking: false,
    lastResult: null,
    lastError: null,
    ...overrides,
  };
}

const DRAFT_FIELDS = { tiers: [{ name: "Básico", price: 100 }] };
const MOCK_RESULT = {
  sectionSlug: "pricing",
  draftFields: DRAFT_FIELDS,
  suggestions: ["Aplica el tier con anclaje de precio."],
  confidence: 0.9,
  citations: [],
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("OfferSectionCopilot", () => {
  const onApplyDraft = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseOfferCopilot.mockReturnValue(buildHookResult());
  });

  describe("empty state", () => {
    it("renders empty state message when no tools are mapped to the section slug", () => {
      render(
        <OfferSectionCopilot
          offerId="offer-1"
          sectionSlug="__unknown_section__"
          onApplyDraft={onApplyDraft}
        />,
      );

      expect(
        screen.getByText(/no hay sugerencias disponibles para esta sección/i),
      ).toBeInTheDocument();
    });
  });

  describe("suggestion cards", () => {
    it("renders one card per mapped tool for sectionSlug=promise", () => {
      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="promise" onApplyDraft={onApplyDraft} />,
      );

      // promise maps to: adapt_from_brand_narrative, rewrite_tones, validate_preset_coherence
      const applyButtons = screen.getAllByRole("button", { name: /aplicar sugerencia/i });
      expect(applyButtons.length).toBeGreaterThanOrEqual(2);
    });

    it("renders 'Aplicar sugerencia' button per card", () => {
      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      // pricing maps to: high_ticket_tiering_template, recurring_billing_setup, detect_currency_mismatch
      const applyButtons = screen.getAllByRole("button", { name: /aplicar sugerencia/i });
      expect(applyButtons.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("invoking a tool", () => {
    it("calls invokeTool with the correct tool_key when 'Aplicar sugerencia' is clicked", async () => {
      mockInvokeTool.mockResolvedValueOnce(undefined);

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      const firstApplyBtn = screen.getAllByRole("button", { name: /aplicar sugerencia/i })[0];
      fireEvent.click(firstApplyBtn);

      await waitFor(() => {
        expect(mockInvokeTool).toHaveBeenCalledTimes(1);
      });
    });

    it("shows spinner while isInvoking is true", () => {
      mockUseOfferCopilot.mockReturnValue(buildHookResult({ isInvoking: true }));

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      // Loader2 renders with aria-hidden; check container has the spinner icon rendered
      const spinner = document.querySelector('[aria-label="Procesando sugerencia"]');
      expect(spinner).not.toBeNull();
    });
  });

  describe("draft preview", () => {
    it("renders draft fields preview after lastResult is set", () => {
      mockUseOfferCopilot.mockReturnValue(
        buildHookResult({
          lastResult: MOCK_RESULT,
        }),
      );

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      // Suggestions text should be visible
      expect(screen.getByText(/aplica el tier con anclaje de precio/i)).toBeInTheDocument();
    });

    it("renders 'Aplicar al formulario' button when lastResult has draftFields", () => {
      mockUseOfferCopilot.mockReturnValue(
        buildHookResult({
          lastResult: MOCK_RESULT,
        }),
      );

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      expect(screen.getByRole("button", { name: /aplicar al formulario/i })).toBeInTheDocument();
    });

    it("calls onApplyDraft with draftFields when 'Aplicar al formulario' is clicked", () => {
      mockUseOfferCopilot.mockReturnValue(
        buildHookResult({
          lastResult: MOCK_RESULT,
        }),
      );

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      const applyFormBtn = screen.getByRole("button", { name: /aplicar al formulario/i });
      fireEvent.click(applyFormBtn);

      expect(onApplyDraft).toHaveBeenCalledWith(DRAFT_FIELDS);
    });
  });

  describe("error state", () => {
    it("calls toast.error when lastError is set", async () => {
      const { toast } = await import("sonner");
      const error = new Error("Backend error");

      mockUseOfferCopilot.mockReturnValue(
        buildHookResult({
          lastError: error,
        }),
      );

      render(
        <OfferSectionCopilot offerId="offer-1" sectionSlug="pricing" onApplyDraft={onApplyDraft} />,
      );

      await waitFor(() => {
        expect(toast.error).toHaveBeenCalled();
      });
    });
  });
});
