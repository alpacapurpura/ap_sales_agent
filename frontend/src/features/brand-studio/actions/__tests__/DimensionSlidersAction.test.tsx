import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { DimensionSlidersAction } from "../DimensionSlidersAction";

import type { PersonalityDimensions } from "@/features/brand-studio/types/personality";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok") }),
}));

const mutateAsync = vi.fn();
vi.mock("@/features/brand-studio/api/personality", () => ({
  useUpdateDimensions: () => ({ mutateAsync, isPending: false }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

const FIXTURE: PersonalityDimensions = {
  energy: 0.5,
  warmth: 0.5,
  humor: 0.25,
  expressiveness: 0.75,
  narrative: 0.5,
  verbosity: 0.5,
};

function renderAction(props: Partial<React.ComponentProps<typeof DimensionSlidersAction>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DimensionSlidersAction value={FIXTURE} onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

describe("DimensionSlidersAction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders one slider per dimension (6 total)", () => {
    renderAction();
    expect(screen.getAllByRole("slider").length).toBe(6);
  });

  it("does not show the save button when nothing has changed", () => {
    renderAction();
    expect(screen.queryByRole("button", { name: /Guardar/i })).toBeNull();
  });

  it("reveals the save button once a slider moves", () => {
    renderAction();
    const firstSlider = screen.getAllByRole("slider")[0];
    fireEvent.keyDown(firstSlider, { key: "ArrowRight" });
    expect(screen.getByRole("button", { name: /Guardar/i })).toBeTruthy();
  });

  it("calls useUpdateDimensions + onChange after a successful save", async () => {
    mutateAsync.mockResolvedValue(undefined);
    const onChange = vi.fn();
    renderAction({ onChange });

    const firstSlider = screen.getAllByRole("slider")[0];
    fireEvent.keyDown(firstSlider, { key: "ArrowRight" });
    fireEvent.click(screen.getByRole("button", { name: /Guardar/i }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalled();
      expect(onChange).toHaveBeenCalled();
    });
  });

  it("does not call onChange when the mutation fails", async () => {
    mutateAsync.mockRejectedValue(new Error("boom"));
    const onChange = vi.fn();
    renderAction({ onChange });

    const firstSlider = screen.getAllByRole("slider")[0];
    fireEvent.keyDown(firstSlider, { key: "ArrowRight" });
    fireEvent.click(screen.getByRole("button", { name: /Guardar/i }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalled();
    });
    expect(onChange).not.toHaveBeenCalled();
  });
});
