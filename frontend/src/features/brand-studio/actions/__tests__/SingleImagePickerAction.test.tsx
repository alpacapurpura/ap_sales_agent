import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { SingleImagePickerAction } from "../SingleImagePickerAction";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok") }),
}));

vi.mock("@/lib/api/assets", () => ({
  assetsApi: {
    list: vi.fn().mockResolvedValue([]),
    upload: vi.fn(),
  },
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <span data-testid="image" data-alt={alt} />,
}));

function renderAction(props: Partial<React.ComponentProps<typeof SingleImagePickerAction>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <SingleImagePickerAction value="" onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

describe("SingleImagePickerAction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the default 'Seleccionar imagen' trigger when empty", () => {
    renderAction();
    expect(screen.getByRole("button", { name: /Seleccionar imagen/i })).toBeTruthy();
  });

  it("renders an image preview when a value is set", () => {
    renderAction({ value: "https://example.com/img.png" });
    const images = screen.getAllByTestId("image");
    expect(images.length).toBeGreaterThan(0);
  });

  it("opens the picker dialog on click", () => {
    renderAction();
    fireEvent.click(screen.getByRole("button", { name: /Seleccionar imagen/i }));
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Galería/i })).toBeTruthy();
    expect(screen.getByRole("tab", { name: /Subir nueva/i })).toBeTruthy();
  });
});
