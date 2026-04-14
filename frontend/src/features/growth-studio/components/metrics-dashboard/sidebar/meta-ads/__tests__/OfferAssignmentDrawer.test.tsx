import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

// Mock config
vi.mock("@/lib/config", () => ({
  config: { api: { baseUrl: "https://api.test.com" } },
}));

// Mock fetchClient
const mockFetchClient = vi.fn();
vi.mock("@/lib/http-client", () => ({
  fetchClient: (...args: unknown[]) => mockFetchClient(...args),
}));

import { OfferAssignmentDrawer } from "../OfferAssignmentDrawer";
import type { AssignmentTarget, AssignmentOffer } from "../OfferAssignmentDrawer";

const OFFERS: AssignmentOffer[] = [
  { id: "off-1", name: "MasterClass", archetype: "PROGRAMA", expectedMetricLabelEs: "Compras" },
  { id: "off-2", name: "Consultoría", archetype: "SERVICIO", expectedMetricLabelEs: "Mensajes" },
];

const TARGETS: AssignmentTarget[] = [
  {
    type: "campaign",
    externalId: "camp-1",
    name: "Sales Master 2026",
    objective: "OUTCOME_SALES",
    currentOfferId: null,
    suggestedOfferId: "off-1",
    suggestedConfidence: "high",
  },
  {
    type: "campaign",
    externalId: "camp-2",
    name: "Tráfico general",
    objective: "OUTCOME_TRAFFIC",
    currentOfferId: null,
    suggestedOfferId: null,
    suggestedConfidence: null,
  },
];

function renderWithClient(ui: React.ReactElement) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

describe("OfferAssignmentDrawer", () => {
  beforeEach(() => {
    mockFetchClient.mockReset();
  });

  it("renders the drawer when open=true with the best-practices block", () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    expect(screen.getByText(/Asociar campañas a offers/i)).toBeInTheDocument();
    expect(screen.getByText(/Cómo organizar tus campañas/i)).toBeInTheDocument();
  });

  it("renders each target with its objective label", () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    expect(screen.getByText("Sales Master 2026")).toBeInTheDocument();
    expect(screen.getByText("Tráfico general")).toBeInTheDocument();
  });

  it('shows "Sugerido" tag on targets with a suggested offer', () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    expect(screen.getByText(/Sugerido/i)).toBeInTheDocument();
  });

  it("shows empty-state message when no targets are provided", () => {
    renderWithClient(
      <OfferAssignmentDrawer open={true} onOpenChange={vi.fn()} targets={[]} offers={OFFERS} />,
    );
    expect(screen.getByText(/No hay campañas sin asignar/i)).toBeInTheDocument();
  });

  it("auto-save footer hint is visible (no manual save button)", () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    // Footer shows the auto-save hint
    expect(screen.getByText(/Cada selección se guarda automáticamente/i)).toBeInTheDocument();
    // No "Guardar N cambios" button any more
    expect(screen.queryByRole("button", { name: /Guardar/i })).toBeNull();
  });

  it("excludes targets that already have an association from the list", () => {
    const mixedTargets: AssignmentTarget[] = [
      {
        type: "campaign",
        externalId: "unassigned-1",
        name: "Sin asignar",
        objective: "OUTCOME_SALES",
        currentOfferId: null,
      },
      {
        type: "campaign",
        externalId: "assigned-1",
        name: "Ya asignada",
        objective: "OUTCOME_TRAFFIC",
        currentOfferId: "off-1",
      },
    ];
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={mixedTargets}
        offers={OFFERS}
      />,
    );
    expect(screen.getByText("Sin asignar")).toBeInTheDocument();
    expect(screen.queryByText("Ya asignada")).toBeNull();
  });

  it("renders an Auto-detectar button", () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={true}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    expect(screen.getByRole("button", { name: /Auto-detectar/i })).toBeInTheDocument();
  });

  it("does not render the sheet when open=false", () => {
    renderWithClient(
      <OfferAssignmentDrawer
        open={false}
        onOpenChange={vi.fn()}
        targets={TARGETS}
        offers={OFFERS}
      />,
    );
    // Sheet portal is hidden — nothing with the heading text should be present
    expect(screen.queryByText(/Asociar campañas a offers/i)).toBeNull();
  });
});
