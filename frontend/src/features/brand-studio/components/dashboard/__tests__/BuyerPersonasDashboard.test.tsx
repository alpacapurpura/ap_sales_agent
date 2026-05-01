import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { BuyerPersonasDashboard } from "../BuyerPersonasDashboard";

import type { BuyerPersona } from "@/lib/api/buyer-persona";

const {
  mockList,
  mockCreate,
  mockSendMessage,
  mockOpenPanel,
  mockRouterPush,
  mockReportEvent,
  navigateMock,
} = vi.hoisted(() => ({
  mockList: vi.fn(),
  mockCreate: vi.fn(),
  mockSendMessage: vi.fn(),
  mockOpenPanel: vi.fn(),
  mockRouterPush: vi.fn(),
  mockReportEvent: vi.fn(),
  navigateMock: vi.fn(),
}));

const TEST_TOKEN = "test-token";
const CREATE_BUTTON = /crear nueva persona/i;
const EMPTY_STATE_TITLE = "Sin Buyer Personas";

vi.mock("@/lib/api/buyer-persona", () => ({
  buyerPersonaApi: {
    list: (...args: unknown[]) => mockList(...args),
    create: (...args: unknown[]) => mockCreate(...args),
  },
}));

vi.mock("@/features/copilot/hooks/use-copilot-chat", () => ({
  useCopilotChat: () => ({
    sendMessage: mockSendMessage,
    sendCardAction: vi.fn(),
    stopStreaming: vi.fn(),
  }),
}));

vi.mock("@/features/copilot/store/copilot-store", () => {
  const state = { isOpen: false, openPanel: mockOpenPanel };
  const useCopilotStore = (selector?: (s: typeof state) => unknown) =>
    selector ? selector(state) : state;
  useCopilotStore.getState = () => state;
  return { useCopilotStore };
});

vi.mock("@/features/copilot/api/copilot-api", () => ({
  reportCopilotEvent: (...args: unknown[]) => mockReportEvent(...args),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue(TEST_TOKEN) }),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ tenantId: "t-1" }),
  useRouter: () => ({ push: mockRouterPush }),
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    navigate: navigateMock,
    isNavigating: false,
    navigateReplace: vi.fn(),
    pendingHref: null,
    runWithOverlay: async <T,>(fn: () => Promise<T>) => fn(),
  }),
}));

function makePersona(overrides: Partial<BuyerPersona> = {}): BuyerPersona {
  return {
    id: "persona-1",
    name: "María la creadora",
    tagline: "Educadora digital",
    scope: "GLOBAL",
    offer_id: null,
    is_primary: true,
    demographics: {},
    psychographics: {},
    pain_points: [],
    desires: [],
    buyer_journey: {},
    purchase_triggers: [],
    anti_patterns: [],
    completeness_score: 65,
    created_at: null,
    updated_at: null,
    ...overrides,
  };
}

function renderDashboard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <BuyerPersonasDashboard />
    </QueryClientProvider>,
  );
}

describe("BuyerPersonasDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders skeletons while loading", () => {
    mockList.mockImplementation(() => new Promise(() => undefined));
    renderDashboard();
    expect(screen.getAllByTestId("persona-skeleton").length).toBeGreaterThan(0);
  });

  it("empty state shows a single AI-led create button", async () => {
    mockList.mockResolvedValue([]);
    renderDashboard();
    await waitFor(() => expect(screen.getByText(EMPTY_STATE_TITLE)).toBeTruthy());
    // Header + EmptyState render the action — both must use the same single button.
    const buttons = screen.getAllByRole("button", { name: CREATE_BUTTON });
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("renders a card per persona with name, tagline, completeness and primary badge", async () => {
    mockList.mockResolvedValue([
      makePersona({
        id: "p-1",
        name: "María",
        tagline: "Creadora",
        is_primary: true,
        completeness_score: 65,
      }),
      makePersona({
        id: "p-2",
        name: "Joven Pro",
        tagline: "Consultor",
        is_primary: false,
        completeness_score: 20,
      }),
    ]);
    renderDashboard();

    await waitFor(() => expect(screen.getByText("María")).toBeTruthy());
    expect(screen.getByText("Joven Pro")).toBeTruthy();
    expect(screen.getByText("Creadora")).toBeTruthy();
    expect(screen.getByText("65%")).toBeTruthy();
    expect(screen.getByText("20%")).toBeTruthy();
    expect(screen.getByText(/Principal/i)).toBeTruthy();
  });

  it("navigates to persona detail on card click", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([makePersona({ id: "p-9", name: "Persona 9" })]);
    renderDashboard();

    const card = await screen.findByRole("button", { name: /Persona 9/i });
    await user.click(card);

    expect(navigateMock).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/p-9");
  });

  it("renders error alert with retry when fetch fails", async () => {
    mockList.mockRejectedValue(new Error("boom"));
    renderDashboard();
    await waitFor(() => expect(screen.getByText(/No se pudieron cargar/i)).toBeTruthy());
    expect(screen.getByRole("button", { name: /reintentar/i })).toBeTruthy();
  });

  it("Crear nueva persona creates the persona, opens copilot panel, sends guided prompt and navigates", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([]);
    mockCreate.mockResolvedValue(makePersona({ id: "smart-id", name: "Nueva persona" }));
    mockSendMessage.mockResolvedValue(undefined);
    renderDashboard();

    await waitFor(() => expect(screen.getByText(EMPTY_STATE_TITLE)).toBeTruthy());
    await user.click(screen.getAllByRole("button", { name: CREATE_BUTTON })[0]);

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith(
        TEST_TOKEN,
        expect.objectContaining({ name: "Nueva persona", scope: "GLOBAL" }),
      ),
    );
    await waitFor(() => expect(mockOpenPanel).toHaveBeenCalled());
    await waitFor(() =>
      expect(mockSendMessage).toHaveBeenCalledWith(expect.stringContaining("Guíame paso a paso")),
    );
    expect(mockSendMessage).toHaveBeenCalledWith(expect.stringContaining("smart-id"));
    expect(mockRouterPush).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/smart-id");
  });

  it("still navigates to detail if guided trigger throws (persona was created)", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([]);
    mockCreate.mockResolvedValue(makePersona({ id: "smart-id" }));
    mockSendMessage.mockRejectedValue(new Error("chat down"));
    renderDashboard();

    await waitFor(() => expect(screen.getByText(EMPTY_STATE_TITLE)).toBeTruthy());
    await user.click(screen.getAllByRole("button", { name: CREATE_BUTTON })[0]);

    await waitFor(() =>
      expect(mockRouterPush).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/smart-id"),
    );
  });

  it("surfaces error and does not navigate when create call fails", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([]);
    mockCreate.mockRejectedValue(new Error("backend 500"));
    renderDashboard();

    await waitFor(() => expect(screen.getByText(EMPTY_STATE_TITLE)).toBeTruthy());
    await user.click(screen.getAllByRole("button", { name: CREATE_BUTTON })[0]);

    await waitFor(() => expect(screen.getByText(/backend 500/i)).toBeTruthy());
    expect(mockOpenPanel).not.toHaveBeenCalled();
    expect(mockSendMessage).not.toHaveBeenCalled();
    expect(mockRouterPush).not.toHaveBeenCalled();
  });

  it("increments default name suffix when personas already exist", async () => {
    const user = userEvent.setup();
    mockList.mockResolvedValue([
      makePersona({ id: "a", name: "Persona A" }),
      makePersona({ id: "b", name: "Persona B" }),
    ]);
    mockCreate.mockResolvedValue(makePersona({ id: "c", name: "Nueva persona 3" }));
    mockSendMessage.mockResolvedValue(undefined);
    renderDashboard();

    await screen.findByText("Persona A");
    await user.click(screen.getAllByRole("button", { name: CREATE_BUTTON })[0]);

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith(
        TEST_TOKEN,
        expect.objectContaining({ name: "Nueva persona 3" }),
      ),
    );
  });
});
