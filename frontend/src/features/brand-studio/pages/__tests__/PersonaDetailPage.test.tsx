import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("next/navigation", () => ({
  useParams: vi.fn(),
}));

const { useParams } = await import("next/navigation");

const useBuyerPersonaMock = vi.fn();
vi.mock("@/features/brand-studio/hooks/use-buyer-persona", () => ({
  useBuyerPersona: () => useBuyerPersonaMock(),
}));

vi.mock("@/features/copilot/api/interview-api", () => ({
  startInterview: vi.fn(),
}));

vi.mock("@/features/copilot/store/copilot-store", () => {
  const state = {
    isOpen: false,
    setSession: vi.fn(),
    setConversationId: vi.fn(),
    addMessage: vi.fn(),
    setSidebarState: vi.fn(),
    connectBridge: vi.fn(),
    disconnectBridge: vi.fn(),
  };
  const useCopilotStore = (selector?: (s: typeof state) => unknown) =>
    selector ? selector(state) : state;
  useCopilotStore.getState = () => state;
  return { useCopilotStore };
});

import { startInterview } from "@/features/copilot/api/interview-api";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";

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
  objections: [],
  preferred_channels: [],
  buyer_journey: {},
  purchase_triggers: [],
  anti_patterns: [],
  completeness_score: 50,
  interview_session_id: null,
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

  it("renders the section title + the persona name when data is present", () => {
    vi.mocked(useParams).mockReturnValue({ tenantId: "t", personaId: "p" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: FULL_PERSONA,
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByRole("heading", { name: /Buyer persona/i })).toBeTruthy();
    expect(screen.getByDisplayValue("María")).toBeTruthy();
  });

  it("wires onStartInterview to startInterview + copilot store", async () => {
    const user = userEvent.setup();
    vi.mocked(useParams).mockReturnValue({ tenantId: "t", personaId: "p-42" } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: { ...FULL_PERSONA, id: "p-42" },
      isLoading: false,
      save: vi.fn(),
    });
    vi.mocked(startInterview).mockResolvedValue({
      session_id: "sess-1",
      conversation_id: "conv-1",
      config: {},
      initial_message: "Hola",
    });

    renderPage();
    await user.click(screen.getByRole("button", { name: /entrevista guiada/i }));

    await waitFor(() =>
      expect(startInterview).toHaveBeenCalledWith("test-token", "buyer_persona", "p-42"),
    );
    const store = useCopilotStore.getState();
    expect(store.setSession).toHaveBeenCalled();
    expect(store.setConversationId).toHaveBeenCalledWith("conv-1");
    expect(store.setSidebarState).toHaveBeenCalledWith("open");
  });

  it("derives the active field from the URL fieldId segment", () => {
    vi.mocked(useParams).mockReturnValue({
      tenantId: "t",
      personaId: "p",
      fieldId: "tagline",
    } as never);
    useBuyerPersonaMock.mockReturnValue({
      persona: { ...FULL_PERSONA, is_primary: false, completeness_score: 0 },
      isLoading: false,
      save: vi.fn(),
    });
    renderPage();
    expect(screen.getByDisplayValue("Creadora digital")).toBeTruthy();
  });
});
