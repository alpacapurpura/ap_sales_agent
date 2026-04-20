/**
 * Smoke test for TestimonialInstancePicker — verifies it renders the list and
 * the create CTA without mocking the full React Query stack (the picker only
 * consumes a thin hook surface).
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { TestimonialInstancePicker } from "../TestimonialInstancePicker";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: async () => null, isSignedIn: false }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn(), forward: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("../../hooks/use-testimonials", () => ({
  useTestimonials: () => ({
    testimonials: [
      {
        id: "t1",
        author_name: "Juana Pérez",
        author_role: "CEO de Alpaca Coffee",
        media_type: "text",
        content: "Excelente servicio",
        rating: 5,
        source_url: null,
        author_avatar_url: null,
      },
      {
        id: "t2",
        author_name: "Carlos López",
        author_role: null,
        media_type: "video",
        content: null,
        rating: null,
        source_url: null,
        author_avatar_url: null,
      },
    ],
    create: vi.fn(),
    isCreating: false,
  }),
}));

function renderPicker(activeId: string | null) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <TestimonialInstancePicker tenantId="tenant-1" activeTestimonialId={activeId} />
    </QueryClientProvider>,
  );
}

describe("TestimonialInstancePicker", () => {
  test("renders section title and create CTA", () => {
    renderPicker(null);
    expect(screen.getByText("Testimonios")).toBeInTheDocument();
    expect(screen.getByText(/Crear nuevo testimonio/i)).toBeInTheDocument();
  });

  test("renders one row per testimonial with author name + role", () => {
    renderPicker(null);
    expect(screen.getByText("Juana Pérez")).toBeInTheDocument();
    expect(screen.getByText("CEO de Alpaca Coffee")).toBeInTheDocument();
    expect(screen.getByText("Carlos López")).toBeInTheDocument();
    // Fallback secondary when author_role absent: media_type for non-text items.
    expect(screen.getByText("video")).toBeInTheDocument();
  });
});
