import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { OnboardingWizard } from "../OnboardingWizard";

// Mock Next.js navigation (required by useOnboardingWizard)
const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

// Mock useBrandSettings
vi.mock("../../../hooks/use-brand-settings", () => ({
  useBrandSettings: () => ({
    settings: null,
    loading: false,
    error: null,
    saving: false,
    refetch: vi.fn(),
  }),
}));

// Mock Clerk auth
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("mock-token") }),
}));

describe("OnboardingWizard", () => {
  it("renders source picker as first step", () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    expect(screen.getByText("Construyamos tu marca")).toBeInTheDocument();
    expect(screen.getByText("Desde tu Website")).toBeInTheDocument();
    expect(screen.getByText("Desde tus Documentos")).toBeInTheDocument();
    expect(screen.getByText("Haciéndolo Juntos")).toBeInTheDocument();
  });

  it("disables continue until a source is selected", () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    const continueBtn = screen.getByRole("button", { name: /continuar/i });
    expect(continueBtn).toBeDisabled();
  });

  it("navigates to website step when website selected", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tu Website"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    expect(screen.getByText("¿Cuál es tu sitio web?")).toBeInTheDocument();
  });

  it("navigates to documents step when documents selected", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tus Documentos"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    expect(screen.getByText("Sube tus documentos")).toBeInTheDocument();
  });

  it("calls onManual when manual link clicked", async () => {
    const onManual = vi.fn();
    render(<OnboardingWizard onComplete={vi.fn()} onManual={onManual} />);

    await userEvent.click(screen.getByText(/prefiero hacerlo manualmente/i));
    expect(onManual).toHaveBeenCalled();
  });

  it("can navigate back from website step", async () => {
    render(<OnboardingWizard onComplete={vi.fn()} onManual={vi.fn()} />);

    await userEvent.click(screen.getByText("Desde tu Website"));
    await userEvent.click(screen.getByRole("button", { name: /continuar/i }));

    // Now on website step
    expect(screen.getByText("¿Cuál es tu sitio web?")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /atrás/i }));

    // Back to source picker
    expect(screen.getByText("Construyamos tu marca")).toBeInTheDocument();
  });
});
