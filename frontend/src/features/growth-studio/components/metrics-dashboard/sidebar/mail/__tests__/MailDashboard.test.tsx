import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, expect, it, vi } from "vitest";

// --- Mocks ---
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("test-token") }),
}));

vi.mock("../../../../../hooks/use-sync-channel", () => ({
  useSyncChannel: () => ({
    sync: vi.fn(),
    isSyncing: false,
    cooldownMinutes: 0,
    result: null,
    error: null,
    reset: vi.fn(),
  }),
}));

vi.mock("../../../../../hooks/use-connection-health", () => ({
  useConnectionHealth: () => ({ data: null, isLoading: false }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "test-tenant" }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

vi.mock("../../../../../hooks/use-metric-catalog", () => ({
  useMetricCatalog: () => ({
    getTooltipData: () => null,
  }),
}));

// Mock tab components to avoid data-fetching concerns in shell test
vi.mock("../tabs/MailPanoramaTab", () => ({
  MailPanoramaTab: () => <div data-testid="panorama-tab">Panorama Content</div>,
}));
vi.mock("../tabs/MailCampanasTab", () => ({
  MailCampanasTab: () => <div data-testid="campanas-tab">Campanas Content</div>,
}));
vi.mock("../tabs/MailAutomatizacionesTab", () => ({
  MailAutomatizacionesTab: () => <div data-testid="auto-tab">Auto Content</div>,
}));
vi.mock("../tabs/MailAudienciaTab", () => ({
  MailAudienciaTab: () => <div data-testid="audiencia-tab">Audiencia Content</div>,
}));
vi.mock("../tabs/MailEntregabilidadV2Tab", () => ({
  MailEntregabilidadV2Tab: () => <div data-testid="entre-tab">Entregabilidad Content</div>,
}));
vi.mock("../tabs/MailCrecimientoTab", () => ({
  MailCrecimientoTab: () => <div data-testid="crec-tab">Crecimiento Content</div>,
}));

import { MailDashboard } from "../MailDashboard";

function Wrapper({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

describe("MailDashboard", () => {
  it("renders the dashboard header with Volver button", () => {
    render(<MailDashboard isRouteBased />, { wrapper: Wrapper });
    expect(screen.getByText("Volver")).toBeInTheDocument();
  });

  it("renders all 6 tabs", () => {
    render(<MailDashboard isRouteBased />, { wrapper: Wrapper });
    expect(screen.getByRole("tab", { name: "Panorama" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Campaña/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Automatizaciones" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Audiencia" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Entregabilidad" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Crecimiento" })).toBeInTheDocument();
  });

  it("renders the period selector", () => {
    render(<MailDashboard isRouteBased />, { wrapper: Wrapper });
    expect(screen.getByText("30 días")).toBeInTheDocument();
    expect(screen.getByText("7 días")).toBeInTheDocument();
    expect(screen.getByText("90 días")).toBeInTheDocument();
  });

  it("renders the dashboard title", () => {
    const { container } = render(<MailDashboard isRouteBased />, { wrapper: Wrapper });
    expect(container.textContent).toContain("Email Marketing");
    expect(container.textContent).toContain("Dashboard");
  });

  it("renders the Panorama tab content by default", () => {
    render(<MailDashboard isRouteBased />, { wrapper: Wrapper });
    expect(screen.getByTestId("panorama-tab")).toBeInTheDocument();
  });
});
