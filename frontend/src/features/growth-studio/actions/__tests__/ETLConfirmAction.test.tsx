/**
 * Tests for ETLConfirmAction component.
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { ETLConfirmAction } from "../ETLConfirmAction";
import { clearRegistry } from "@/lib/form-runtime/actions";

vi.mock("@/features/tenant/context/tenant-locale-context", () => ({
  useTenantLocale: () => ({ currency: "USD", timezone: "America/Lima" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("../api/etl-api", () => ({
  triggerEtlChannel: vi.fn().mockResolvedValue({ ok: true }),
}));

describe("ETLConfirmAction", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("renders confirm prompt with role=alert", () => {
    render(
      <ETLConfirmAction
        value={{ channel: "meta-ads", confirm_message: "¿Deseas iniciar la actualización?" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders confirm_message text", () => {
    render(
      <ETLConfirmAction
        value={{ channel: "meta-ads", confirm_message: "¿Deseas iniciar la actualización?" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/Deseas iniciar/)).toBeInTheDocument();
  });

  it("renders a confirm button", () => {
    render(
      <ETLConfirmAction
        value={{ channel: "meta-ads", confirm_message: "¿Confirmar?" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("renders channel name", () => {
    render(
      <ETLConfirmAction
        value={{ channel: "email-nurture", confirm_message: "¿Actualizar?" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/email-nurture/i)).toBeInTheDocument();
  });
});
