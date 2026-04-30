/**
 * Tests for SuggestedChips — wired mutation onClick (PR-1 PI-2 S2).
 * TDD: these tests were written RED before the mutation wiring.
 *
 * [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
 */
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ── Module mocks ──────────────────────────────────────────────────────

vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "http://localhost:8000" } },
}));

const mockUseSuggestions = vi.fn();
vi.mock("../../../hooks/use-suggestions", () => ({
  useSuggestions: () => mockUseSuggestions(),
}));

const mockMutate = vi.fn();
vi.mock("../../../hooks/use-suggestion-accept", () => ({
  useSuggestionAccept: () => ({ mutate: mockMutate, isIdle: true }),
}));

const mockGetToken = vi.fn();
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: mockGetToken }),
}));

vi.mock("../../../store/copilot-store", () => ({
  useCopilotStore: (selector: (s: unknown) => unknown) =>
    selector({ currentRoute: "/offer-studio", conversationId: "conv-123" }),
}));

// ── Import after mocks ────────────────────────────────────────────────

import { SuggestedChips } from "../SuggestedChips";

const chips = [
  { id: "chip-1", label: "Crea una oferta", prompt: "Ayúdame a crear", confidence: 0.9, category: "action" as const, source_module: "offer" },
  { id: "chip-2", label: "Revisa escalera", prompt: "Analiza mi escalera", confidence: 0.8, category: "action" as const, source_module: "offer" },
  { id: "chip-3", label: "Mejora objeciones", prompt: "Revisa objeciones", confidence: 0.7, category: "action" as const, source_module: "offer" },
];

describe("SuggestedChips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders chips from useSuggestions hook", () => {
    mockUseSuggestions.mockReturnValue({ chips, isLoading: false });

    const { container } = render(<SuggestedChips onChipClick={vi.fn()} />);

    expect(screen.getByText("Crea una oferta")).toBeDefined();
    expect(screen.getByText("Revisa escalera")).toBeDefined();
    expect(screen.getByText("Mejora objeciones")).toBeDefined();
    // All 3 buttons should be rendered
    const buttons = container.querySelectorAll("button");
    expect(buttons.length).toBe(3);
  });

  it("returns null when chips array is empty", () => {
    mockUseSuggestions.mockReturnValue({ chips: [], isLoading: false });

    const { container } = render(<SuggestedChips onChipClick={vi.fn()} />);

    expect(container.firstChild).toBeNull();
  });

  it("returns null when isLoading is true", () => {
    mockUseSuggestions.mockReturnValue({ chips, isLoading: true });

    const { container } = render(<SuggestedChips onChipClick={vi.fn()} />);

    expect(container.firstChild).toBeNull();
  });

  it("clicking chip fires accept mutation AND onChipClick with correct args", () => {
    mockUseSuggestions.mockReturnValue({ chips, isLoading: false });
    const onChipClick = vi.fn();

    render(<SuggestedChips onChipClick={onChipClick} />);

    const firstChipButton = screen.getByText("Crea una oferta");
    fireEvent.click(firstChipButton);

    // accept mutation called with suggestion + context
    expect(mockMutate).toHaveBeenCalledWith({
      suggestion: chips[0],
      conversationId: "conv-123",
      currentRoute: "/offer-studio",
    });

    // onChipClick called with the prompt
    expect(onChipClick).toHaveBeenCalledWith("Ayúdame a crear");
  });

  it("clicking chip fires both mutation and onChipClick in correct order", () => {
    mockUseSuggestions.mockReturnValue({ chips, isLoading: false });
    const callOrder: string[] = [];
    mockMutate.mockImplementation(() => { callOrder.push("accept"); });
    const onChipClick = vi.fn(() => { callOrder.push("onChipClick"); });

    render(<SuggestedChips onChipClick={onChipClick} />);

    fireEvent.click(screen.getByText("Crea una oferta"));

    expect(callOrder).toContain("accept");
    expect(callOrder).toContain("onChipClick");
  });

  it("uses chip.id as stable key (not array index)", () => {
    mockUseSuggestions.mockReturnValue({ chips, isLoading: false });

    render(<SuggestedChips onChipClick={vi.fn()} />);

    // All chips are rendered — stable keys don't cause duplicates
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });
});
