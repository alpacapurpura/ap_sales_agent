import { render, screen, fireEvent, act } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";

import { AutosaveBanner } from "../AutosaveBanner";

describe("AutosaveBanner", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders null when status is idle", () => {
    const { container } = render(<AutosaveBanner status="idle" />);
    expect(container.firstChild).toBeNull();
  });

  it("shows Guardando… while saving", () => {
    render(<AutosaveBanner status="saving" />);
    expect(screen.getByText(/Guardando/i)).toBeTruthy();
  });

  it("shows Guardado then fades after 2s", () => {
    vi.useFakeTimers();
    const { rerender } = render(<AutosaveBanner status="saving" />);
    rerender(<AutosaveBanner status="saved" />);
    expect(screen.getByText(/Guardado/i)).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(2100);
    });

    expect(screen.queryByText(/Guardado/i)).toBeNull();
  });

  it("shows error message and retry button", () => {
    const onRetry = vi.fn();
    render(<AutosaveBanner status="error" error={new Error("api down")} onRetry={onRetry} />);
    expect(screen.getByText(/api down/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Reintentar/i }));
    expect(onRetry).toHaveBeenCalled();
  });
});
