import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as React from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { CampaignNewClient } from "../components/CampaignNewClient";

// Mock next/navigation
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
    back: vi.fn(),
    replace: vi.fn(),
  }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

// Mock campaign mutations
const mockCreateCampaign = vi.fn().mockResolvedValue({ id: "camp-123" });
const mockAddStep = vi.fn().mockResolvedValue({ id: "step-1" });
const mockSchedule = vi.fn().mockResolvedValue({});

vi.mock("../api/use-create-campaign-mutation", () => ({
  useCreateCampaignMutation: () => ({
    mutateAsync: mockCreateCampaign,
    isPending: false,
  }),
}));

vi.mock("../api/use-add-campaign-step-mutation", () => ({
  useAddCampaignStepMutation: () => ({
    mutateAsync: mockAddStep,
    isPending: false,
  }),
}));

vi.mock("../api/use-schedule-campaign-mutation", () => ({
  useScheduleCampaignMutation: () => ({
    mutateAsync: mockSchedule,
    isPending: false,
  }),
}));

// Mock SmartDateTimePicker (complex component not needed for unit test)
vi.mock("@/components/ui/smart-datetime-picker", () => ({
  SmartDateTimePicker: ({ onChange }: { onChange: (v: string) => void }) => (
    <input
      data-testid="datetime-picker"
      onChange={(e) => onChange(e.target.value)}
      aria-label="Programar envío"
    />
  ),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("CampaignNewClient", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location.pathname for tenant routing
    Object.defineProperty(window, "location", {
      value: { ...window.location, pathname: "/tenant-123/sales/campanas/nuevo" },
      writable: true,
    });
  });

  it("shows warning and back button when segmentId is null", () => {
    render(<CampaignNewClient segmentId={null} />, { wrapper: createWrapper() });

    expect(screen.getByText(/debes seleccionar un segmento/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /volver/i })).toBeInTheDocument();
  });

  it("renders form when segmentId provided", () => {
    render(<CampaignNewClient segmentId="seg-abc" />, { wrapper: createWrapper() });

    expect(screen.getByLabelText(/nombre de la campaña/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /crear campaña/i })).toBeInTheDocument();
  });

  it("submits POST campaign then POST step", async () => {
    const user = userEvent.setup();

    render(<CampaignNewClient segmentId="seg-abc" />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/nombre de la campaña/i), "Campaña Test");
    await user.click(screen.getByRole("button", { name: /crear campaña/i }));

    await waitFor(() => {
      expect(mockCreateCampaign).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Campaña Test",
          campaign_type: "AGENT_CONVERSATION",
          segment_id: "seg-abc",
          channel_priority: ["telegram"],
        }),
      );
    });

    await waitFor(() => {
      expect(mockAddStep).toHaveBeenCalledWith(
        expect.objectContaining({
          step_type: "CALL_SUBAGENT_BRIEF",
          step_index: 0,
          step_config: {},
        }),
      );
    });
  });

  it("does not call schedule mutation when no date set", async () => {
    const user = userEvent.setup();

    render(<CampaignNewClient segmentId="seg-abc" />, { wrapper: createWrapper() });

    await user.type(screen.getByLabelText(/nombre de la campaña/i), "Draft Campaign");
    await user.click(screen.getByRole("button", { name: /crear campaña/i }));

    await waitFor(() => {
      expect(mockCreateCampaign).toHaveBeenCalled();
    });

    expect(mockSchedule).not.toHaveBeenCalled();
  });

  it("shows validation error when name is empty", async () => {
    const user = userEvent.setup();

    render(<CampaignNewClient segmentId="seg-abc" />, { wrapper: createWrapper() });

    await user.click(screen.getByRole("button", { name: /crear campaña/i }));

    await waitFor(() => {
      expect(screen.getByText(/nombre es requerido/i)).toBeInTheDocument();
    });
  });
});
