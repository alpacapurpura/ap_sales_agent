import { renderHook, act, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { useOfferCopilot } from "../use-offer-copilot";

// ── Mocks ────────────────────────────────────────────────────────────────────

// Mock the api module so no real HTTP calls are made.
vi.mock("../../api/section-tools-api", () => ({
  invokeOfferSectionTool: vi.fn(),
}));

// We mock the mutation at the React Query layer so we can control the
// lifecycle (idle → loading → success / error) deterministically.
const mockMutateAsync = vi.fn();
const mockMutation = {
  mutateAsync: mockMutateAsync,
  isPending: false,
  reset: vi.fn(),
};

vi.mock("@tanstack/react-query", async (importActual) => {
  const actual = await importActual<typeof import("@tanstack/react-query")>();
  return {
    ...actual,
    useMutation: vi.fn(() => mockMutation),
  };
});

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok-123") }),
}));

// ── Types ─────────────────────────────────────────────────────────────────────

import type { OfferCopilotResult } from "../use-offer-copilot";

// ── Fixtures ─────────────────────────────────────────────────────────────────

const OFFER_ID = "offer-abc";
const SECTION_SLUG = "pricing";

const MOCK_RESULT: OfferCopilotResult = {
  sectionSlug: "pricing",
  draftFields: { tiers: [{ name: "Básico", price: 100 }] },
  suggestions: ["Aplica el tier con anclaje de precio."],
  confidence: 0.9,
  citations: ["brand:identity"],
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useOfferCopilot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMutation.isPending = false;
  });

  describe("initial state", () => {
    it("returns null lastResult and null lastError on mount", () => {
      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      expect(result.current.lastResult).toBeNull();
      expect(result.current.lastError).toBeNull();
      expect(result.current.isInvoking).toBe(false);
    });

    it("exposes invokeTool function", () => {
      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      expect(typeof result.current.invokeTool).toBe("function");
    });
  });

  describe("happy path — invokeTool", () => {
    it("calls mutateAsync and populates lastResult on success", async () => {
      mockMutateAsync.mockResolvedValueOnce(MOCK_RESULT);

      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      await act(async () => {
        await result.current.invokeTool("high_ticket_tiering_template");
      });

      expect(mockMutateAsync).toHaveBeenCalledWith({
        toolKey: "high_ticket_tiering_template",
        toolArgs: {},
      });

      await waitFor(() => {
        expect(result.current.lastResult).toEqual(MOCK_RESULT);
        expect(result.current.lastError).toBeNull();
      });
    });

    it("passes toolArgs through to mutateAsync", async () => {
      mockMutateAsync.mockResolvedValueOnce(MOCK_RESULT);

      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      await act(async () => {
        await result.current.invokeTool("high_ticket_tiering_template", { key: "val" });
      });

      expect(mockMutateAsync).toHaveBeenCalledWith({
        toolKey: "high_ticket_tiering_template",
        toolArgs: { key: "val" },
      });
    });
  });

  describe("error path", () => {
    it("populates lastError when mutateAsync rejects", async () => {
      const error = new Error("Backend 500");
      mockMutateAsync.mockRejectedValueOnce(error);

      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      await act(async () => {
        try {
          await result.current.invokeTool("high_ticket_tiering_template");
        } catch {
          // swallowed intentionally — hook captures the error
        }
      });

      await waitFor(() => {
        expect(result.current.lastError).toEqual(error);
        expect(result.current.lastResult).toBeNull();
        expect(result.current.isInvoking).toBe(false);
      });
    });
  });

  describe("isInvoking reflects pending state", () => {
    it("is true when useMutation.isPending is true", () => {
      mockMutation.isPending = true;

      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      expect(result.current.isInvoking).toBe(true);
    });
  });

  describe("reset on prop change", () => {
    it("clears lastResult when sectionSlug changes", async () => {
      mockMutateAsync.mockResolvedValueOnce(MOCK_RESULT);

      const { result, rerender } = renderHook(
        ({ sectionSlug }) => useOfferCopilot({ offerId: OFFER_ID, sectionSlug }),
        { initialProps: { sectionSlug: "pricing" } },
      );

      await act(async () => {
        await result.current.invokeTool("high_ticket_tiering_template");
      });

      await waitFor(() => {
        expect(result.current.lastResult).not.toBeNull();
      });

      // Change sectionSlug — lastResult and lastError should clear
      rerender({ sectionSlug: "identity" });

      await waitFor(() => {
        expect(result.current.lastResult).toBeNull();
        expect(result.current.lastError).toBeNull();
      });
    });

    it("clears lastResult when offerId changes", async () => {
      mockMutateAsync.mockResolvedValueOnce(MOCK_RESULT);

      const { result, rerender } = renderHook(
        ({ offerId }) => useOfferCopilot({ offerId, sectionSlug: SECTION_SLUG }),
        { initialProps: { offerId: "offer-abc" } },
      );

      await act(async () => {
        await result.current.invokeTool("high_ticket_tiering_template");
      });

      await waitFor(() => {
        expect(result.current.lastResult).not.toBeNull();
      });

      // Change offerId — lastResult and lastError should clear
      rerender({ offerId: "offer-xyz" });

      await waitFor(() => {
        expect(result.current.lastResult).toBeNull();
        expect(result.current.lastError).toBeNull();
      });
    });
  });

  describe("idempotency — sequential invocations", () => {
    it("second invocation replaces lastResult without collision", async () => {
      const result1: OfferCopilotResult = { ...MOCK_RESULT, sectionSlug: "pricing" };
      const result2: OfferCopilotResult = {
        ...MOCK_RESULT,
        sectionSlug: "pricing",
        draftFields: { updated: true },
      };

      mockMutateAsync.mockResolvedValueOnce(result1).mockResolvedValueOnce(result2);

      const { result } = renderHook(() =>
        useOfferCopilot({ offerId: OFFER_ID, sectionSlug: SECTION_SLUG }),
      );

      await act(async () => {
        await result.current.invokeTool("high_ticket_tiering_template");
      });

      await waitFor(() => {
        expect(result.current.lastResult).toEqual(result1);
      });

      await act(async () => {
        await result.current.invokeTool("recurring_billing_setup");
      });

      await waitFor(() => {
        expect(result.current.lastResult).toEqual(result2);
      });
    });
  });
});
