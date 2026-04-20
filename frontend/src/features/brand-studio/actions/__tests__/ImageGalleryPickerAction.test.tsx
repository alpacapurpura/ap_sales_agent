import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ImageGalleryPickerAction } from "../ImageGalleryPickerAction";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok") }),
}));

vi.mock("@/lib/api/assets", () => ({
  assetsApi: { list: vi.fn().mockResolvedValue([]), upload: vi.fn() },
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <span data-testid="image" data-alt={alt} />,
}));

function renderAction(props: Partial<React.ComponentProps<typeof ImageGalleryPickerAction>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <ImageGalleryPickerAction value={null} onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

describe("ImageGalleryPickerAction", () => {
  it("renders the empty-state affordance when no images are selected", () => {
    renderAction();
    expect(screen.getByText(/Sin imágenes asociadas/i)).toBeTruthy();
  });

  it("shows the selected count in the header", () => {
    renderAction({ value: ["https://a.png", "https://b.png"] });
    expect(screen.getByText(/Galería \(2\/5\)/)).toBeTruthy();
  });

  it("removes an image when the trash button is clicked", () => {
    const onChange = vi.fn();
    renderAction({ value: ["https://a.png", "https://b.png"], onChange });
    const [removeA] = screen.getAllByRole("button", { name: /Quitar/i });
    fireEvent.click(removeA);
    expect(onChange).toHaveBeenCalledWith(["https://b.png"]);
  });

  it("opens the picker dialog with both tabs", () => {
    renderAction();
    fireEvent.click(screen.getByRole("button", { name: /Gestionar galería/i }));
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Galería de marca/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Subir nueva/i })).toBeTruthy();
  });
});
