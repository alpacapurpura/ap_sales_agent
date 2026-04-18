import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { PresetCatalogAction } from "../PresetCatalogAction";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok") }),
}));

const presetsMock = vi.fn();
const selectMutate = vi.fn();
vi.mock("@/features/brand-studio/api/personality", () => ({
  usePersonalityPresets: () => presetsMock(),
  useSelectPreset: () => ({
    mutateAsync: selectMutate,
    isPending: false,
  }),
}));

vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

function renderAction(props: Partial<React.ComponentProps<typeof PresetCatalogAction>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <PresetCatalogAction value={null} onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

describe("PresetCatalogAction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state", () => {
    presetsMock.mockReturnValue({ data: undefined, isLoading: true, error: null });
    renderAction();
    expect(screen.getByRole("status").textContent).toMatch(/Cargando/i);
  });

  it("renders error alert when presets fail to load", () => {
    presetsMock.mockReturnValue({ data: undefined, isLoading: false, error: new Error("x") });
    renderAction();
    expect(screen.getByRole("alert").textContent).toMatch(/No se pudieron cargar/);
  });

  it("renders every preset and highlights the one matching value", () => {
    presetsMock.mockReturnValue({
      data: [
        { key: "sage", name: "Sage", description: "wise", icon: "🧙", sample_message: "hm" },
        { key: "hero", name: "Hero", description: "brave", icon: "🦸", sample_message: "lets go" },
      ],
      isLoading: false,
      error: null,
    });
    renderAction({ value: "hero" });
    expect(screen.getByRole("button", { name: /Sage/ }).getAttribute("aria-pressed")).toBe("false");
    expect(screen.getByRole("button", { name: /Hero/ }).getAttribute("aria-pressed")).toBe("true");
  });

  it("calls useSelectPreset + onChange after click, and shows success toast", async () => {
    presetsMock.mockReturnValue({
      data: [{ key: "sage", name: "Sage", description: "d", icon: "🧙", sample_message: "h" }],
      isLoading: false,
      error: null,
    });
    selectMutate.mockResolvedValue(undefined);
    const onChange = vi.fn();
    renderAction({ onChange });

    fireEvent.click(screen.getByRole("button", { name: /Sage/ }));

    await waitFor(() => {
      expect(selectMutate).toHaveBeenCalledWith("sage");
      expect(onChange).toHaveBeenCalledWith("sage");
    });
  });

  it("does not call onChange when the mutation fails", async () => {
    presetsMock.mockReturnValue({
      data: [{ key: "sage", name: "Sage", description: "d", icon: "🧙", sample_message: "h" }],
      isLoading: false,
      error: null,
    });
    selectMutate.mockRejectedValue(new Error("boom"));
    const onChange = vi.fn();
    renderAction({ onChange });

    fireEvent.click(screen.getByRole("button", { name: /Sage/ }));

    await waitFor(() => {
      expect(selectMutate).toHaveBeenCalled();
    });
    expect(onChange).not.toHaveBeenCalled();
  });
});
