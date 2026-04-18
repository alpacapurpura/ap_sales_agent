import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { PersonaDetailPage } from "../PersonaDetailPage";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
}));

const { useParams } = await import("next/navigation");

const useBuyerPersonaMock = vi.fn();
vi.mock("@/features/brand-studio/hooks/use-buyer-persona", () => ({
  useBuyerPersona: () => useBuyerPersonaMock(),
}));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PersonaDetailPage />
    </QueryClientProvider>,
  );
}

describe("PersonaDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a guidance message when there is no personaId in the route", () => {
    vi.mocked(useParams).mockReturnValue({ tenantId: "t" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: null,
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByText(/No se especificó/i)).toBeTruthy();
  });

  it("renders 'Persona no encontrada' when the hook resolves to no persona", () => {
    vi.mocked(useParams).mockReturnValue({ tenantId: "t", personaId: "p" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: null,
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByText(/Persona no encontrada/)).toBeTruthy();
  });

  it("renders the section title + the persona name when data is present", () => {
    vi.mocked(useParams).mockReturnValue({ tenantId: "t", personaId: "p" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: {
        id: "p",
        name: "María",
        tagline: "Creadora digital",
        scope: "GLOBAL",
        offer_id: null,
        is_primary: true,
        demographics: { age_range: "28-45" },
        psychographics: {},
        pain_points: [],
        desires: [],
        objections: [],
        preferred_channels: [],
        buyer_journey: {},
        purchase_triggers: [],
        anti_patterns: [],
        completeness_score: 0.5,
        interview_session_id: null,
        created_at: null,
        updated_at: null,
      },
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByRole("heading", { name: /Buyer persona/i })).toBeTruthy();
    expect(screen.getByDisplayValue("María")).toBeTruthy();
  });

  it("derives the active field from the URL fieldId segment", () => {
    vi.mocked(useParams).mockReturnValue({
      tenantId: "t",
      personaId: "p",
      fieldId: "tagline",
    } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: {
        id: "p",
        name: "María",
        tagline: "Creadora digital",
        demographics: {},
        psychographics: {},
        pain_points: [],
        desires: [],
        objections: [],
        preferred_channels: [],
        buyer_journey: {},
        purchase_triggers: [],
        anti_patterns: [],
        completeness_score: 0,
        interview_session_id: null,
        scope: "GLOBAL",
        offer_id: null,
        is_primary: false,
        created_at: null,
        updated_at: null,
      },
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByDisplayValue("Creadora digital")).toBeTruthy();
  });
});
