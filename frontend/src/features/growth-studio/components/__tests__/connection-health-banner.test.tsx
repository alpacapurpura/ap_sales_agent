import { render, screen } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) =>
    React.createElement("a", { href, "data-testid": "link" }, children),
}));

vi.mock("next/navigation", () => ({
  useParams: () => ({ tenantId: "test-tenant" }),
}));

// ── Import after mocks ──────────────────────────────────────────────────
import { ConnectionHealthBanner } from "../connection-health-banner";

describe("ConnectionHealthBanner", () => {
  it('renders nothing when status is "healthy"', () => {
    const { container } = render(
      <ConnectionHealthBanner
        status="healthy"
        channelSlug="meta-ads"
        message="Conexión activa y saludable."
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it('renders yellow warning banner when status is "expiring_soon"', () => {
    render(
      <ConnectionHealthBanner
        status="expiring_soon"
        channelSlug="meta-ads"
        message="El token vence en 5 día(s)."
        expiresAt="2026-04-13T00:00:00Z"
      />,
    );

    expect(screen.getByText(/El token vence en 5 día\(s\)/)).toBeDefined();
    const link = screen.getByRole("link");
    expect(link.textContent).toContain("Reconectar");
  });

  it('renders red error banner when status is "expired"', () => {
    render(
      <ConnectionHealthBanner
        status="expired"
        channelSlug="meta-ads"
        message="El token ha expirado."
      />,
    );

    expect(screen.getByText(/El token ha expirado/)).toBeDefined();
    const link = screen.getByRole("link");
    expect(link.textContent).toContain("Reconectar");
  });

  it('renders blue info banner when status is "not_connected"', () => {
    render(
      <ConnectionHealthBanner
        status="not_connected"
        channelSlug="meta-ads"
        message="No hay conexión activa para este canal."
      />,
    );

    expect(screen.getByText(/No hay conexión activa/)).toBeDefined();
    const link = screen.getByRole("link");
    expect(link.textContent).toContain("Conectar");
  });

  it("renders nothing for unknown/undefined status (defense-in-depth)", () => {
    // E2E mocks or future backend changes may produce unexpected status values.
    // The component must never crash — it should degrade to invisible.
    const { container: c1 } = render(
      <ConnectionHealthBanner
        status={"unknown_value" as any}
        channelSlug="meta-ads"
        message="Unexpected status"
      />,
    );
    expect(c1.innerHTML).toBe("");

    const { container: c2 } = render(
      <ConnectionHealthBanner
        status={undefined as any}
        channelSlug="meta-ads"
        message="Undefined status"
      />,
    );
    expect(c2.innerHTML).toBe("");
  });

  it("links to /connections page in all non-healthy cases", () => {
    const { unmount } = render(
      <ConnectionHealthBanner
        status="expired"
        channelSlug="meta-ads"
        message="El token ha expirado."
      />,
    );

    const link = screen.getByRole("link");
    expect(link.getAttribute("href")).toContain("/connections");
    unmount();

    render(
      <ConnectionHealthBanner
        status="expiring_soon"
        channelSlug="meta-ads"
        message="El token vence en 3 día(s)."
      />,
    );

    const link2 = screen.getByRole("link");
    expect(link2.getAttribute("href")).toContain("/connections");
  });
});
