import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
  usePathname: () => "/t/brand-studio/publico/persona/p",
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

const useBuyerPersonasMock = vi.fn(() => ({
  personas: [],
  isLoading: false,
  create: vi.fn().mockResolvedValue({ id: "new" }),
  patch: vi.fn(),
  remove: vi.fn(),
  isCreating: false,
  isPatching: false,
  error: null,
}));
vi.mock("@/features/brand-studio/hooks/use-buyer-personas", () => ({
  useBuyerPersonas: () => useBuyerPersonasMock(),
}));

// Mock the shared guided-entity-creation hook so the test does not need
// ClerkProvider, the copilot store, the chat API or the SSE stream — those
// belong to the hook's own unit test, not to PersonaDetailPage.
vi.mock("@/features/copilot/hooks/use-guided-entity-creation", () => ({
  useGuidedEntityCreation: () => ({
    create: vi.fn().mockResolvedValue(undefined),
    creating: false,
    error: null,
  }),
}));

const { useParams, useSearchParams } = await import("next/navigation");

const useBuyerPersonaMock = vi.fn();
vi.mock("@/features/brand-studio/hooks/use-buyer-persona", () => ({
  useBuyerPersona: () => useBuyerPersonaMock(),
}));

import { PersonaDetailPage } from "../PersonaDetailPage";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PersonaDetailPage />
    </QueryClientProvider>,
  );
}

const FULL_PERSONA = {
  id: "p",
  name: "María",
  tagline: "Creadora digital",
  scope: "GLOBAL" as const,
  offer_id: null,
  is_primary: true,
  demographics: { age_range: "28-45" },
  psychographics: {},
  pain_points: [],
  desires: [],
  buyer_journey: {},
  purchase_triggers: [],
  anti_patterns: [],
  completeness_score: 50,
  created_at: null,
  updated_at: null,
};

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

  it("renders the persona name field when data is present", () => {
    vi.mocked(useParams).mockReturnValue({ tenantId: "t", personaId: "p" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: FULL_PERSONA,
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByDisplayValue("María")).toBeTruthy();
  });

  it("derives the active field from the ?field= query parameter", () => {
    vi.mocked(useParams).mockReturnValue({
      tenantId: "t",
      personaId: "p",
    } as never);
    vi.mocked(useSearchParams).mockReturnValue(new URLSearchParams({ field: "tagline" }) as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: { ...FULL_PERSONA, is_primary: false, completeness_score: 0 },
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByDisplayValue("Creadora digital")).toBeTruthy();
  });
});
