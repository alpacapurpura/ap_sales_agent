import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DomainStatusBadge } from "../components/DomainStatusBadge";

describe("DomainStatusBadge", () => {
  it('renders "Activo" for active status', () => {
    render(<DomainStatusBadge status="active" />);
    expect(screen.getByText("Activo")).toBeInTheDocument();
  });

  it('renders "Pendiente" for pending_verification status', () => {
    render(<DomainStatusBadge status="pending_verification" />);
    expect(screen.getByText("Pendiente")).toBeInTheDocument();
  });

  it('renders "Verificando" for verifying status with animate-pulse class', () => {
    const { container } = render(<DomainStatusBadge status="verifying" />);
    expect(screen.getByText("Verificando")).toBeInTheDocument();
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("animate-pulse");
  });

  it('renders "Fallido" for failed status', () => {
    render(<DomainStatusBadge status="failed" />);
    expect(screen.getByText("Fallido")).toBeInTheDocument();
  });

  it('renders "Suspendido" for suspended status', () => {
    render(<DomainStatusBadge status="suspended" />);
    expect(screen.getByText("Suspendido")).toBeInTheDocument();
  });

  it("merges custom className with badge classes", () => {
    const { container } = render(<DomainStatusBadge status="active" className="my-custom" />);
    const badge = container.firstChild as HTMLElement;
    expect(badge.className).toContain("my-custom");
  });
});
