import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AutoSaveIndicator } from "../auto-save-indicator";

describe("AutoSaveIndicator", () => {
  it("renders nothing when state is 'idle'", () => {
    const { container } = render(<AutoSaveIndicator state="idle" />);
    expect(container.firstChild).toBeNull();
  });

  it("renders 'Guardando...' when state is 'saving'", () => {
    render(<AutoSaveIndicator state="saving" />);
    expect(screen.getByText(/Guardando\.\.\./)).toBeInTheDocument();
  });

  it("renders 'Guardado hace' when state is 'saved'", () => {
    render(<AutoSaveIndicator state="saved" lastSavedAt={new Date(Date.now() - 5_000)} />);
    expect(screen.getByText(/Guardado/)).toBeInTheDocument();
  });

  it("renders an error with retry button when state is 'error'", () => {
    const onRetry = vi.fn();
    render(<AutoSaveIndicator state="error" onRetry={onRetry} />);
    expect(screen.getByText(/Error al guardar/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Reintentar/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
