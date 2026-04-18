import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { LogoKitAction } from "../LogoKitAction";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("tok") }),
}));

vi.mock("@/lib/api/assets", () => ({
  assetsApi: { list: vi.fn(), upload: vi.fn() },
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <span data-testid="image" data-alt={alt} />,
}));

function renderKit(props: Partial<React.ComponentProps<typeof LogoKitAction>> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <LogoKitAction value={null} onChange={vi.fn()} {...props} />
    </QueryClientProvider>,
  );
}

describe("LogoKitAction", () => {
  it("renders 4 logo-variant slots", () => {
    renderKit();
    expect(screen.getByText(/Logo principal/i)).toBeTruthy();
    expect(screen.getByText(/Isotipo/i)).toBeTruthy();
    expect(screen.getByText(/Para fondo oscuro/i)).toBeTruthy();
    expect(screen.getByText(/Para fondo claro/i)).toBeTruthy();
  });

  it("shows upload affordance when every slot is empty", () => {
    renderKit();
    expect(screen.getAllByText(/Subir/i).length).toBe(4);
  });

  it("renders a preview image for each populated slot", () => {
    renderKit({
      value: {
        primary: "https://example.com/p.png",
        dark_mode: "https://example.com/d.png",
      },
    });
    const images = screen.getAllByTestId("image");
    expect(images.length).toBeGreaterThanOrEqual(2);
  });
});
