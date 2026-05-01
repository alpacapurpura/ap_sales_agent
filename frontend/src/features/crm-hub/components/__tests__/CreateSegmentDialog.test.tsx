import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import * as React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { CreateSegmentDialog } from "../CreateSegmentDialog";

// Mock the mutation hook
vi.mock("@/features/crm-hub/api/use-create-segment-mutation", () => ({
  useCreateSegmentMutation: vi.fn(() => ({
    mutateAsync: vi.fn().mockResolvedValue({ id: "seg-123" }),
    isPending: false,
    reset: vi.fn(),
  })),
}));

// Mock sonner
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe("CreateSegmentDialog", () => {
  let onOpenChange: (open: boolean) => void;
  let onSuccess: (segmentId: string, segmentName: string) => void;

  beforeEach(() => {
    onOpenChange = vi.fn() as unknown as (open: boolean) => void;
    onSuccess = vi.fn() as unknown as (segmentId: string, segmentName: string) => void;
  });

  it("renders form fields when open", () => {
    render(
      <CreateSegmentDialog
        open
        onOpenChange={onOpenChange}
        selectedLeadIds={["lead-1", "lead-2"]}
        onSuccess={onSuccess}
      />,
      { wrapper: createWrapper() },
    );

    expect(screen.getByLabelText(/nombre del segmento/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/descripción/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /crear segmento/i })).toBeInTheDocument();
  });

  it("shows correct lead count in description", () => {
    render(
      <CreateSegmentDialog
        open
        onOpenChange={onOpenChange}
        selectedLeadIds={["lead-1", "lead-2", "lead-3"]}
        onSuccess={onSuccess}
      />,
      { wrapper: createWrapper() },
    );

    expect(screen.getByText(/3 contactos seleccionados/i)).toBeInTheDocument();
  });

  it("submits with STATIC segment_type and correct lead_ids", async () => {
    const { useCreateSegmentMutation } =
      await import("@/features/crm-hub/api/use-create-segment-mutation");
    const mutateAsync = vi.fn().mockResolvedValue({ id: "seg-456" });
    vi.mocked(useCreateSegmentMutation).mockReturnValue({
      mutateAsync,
      isPending: false,
      reset: vi.fn(),
    } as unknown as ReturnType<typeof useCreateSegmentMutation>);

    const user = userEvent.setup();

    render(
      <CreateSegmentDialog
        open
        onOpenChange={onOpenChange}
        selectedLeadIds={["lead-a", "lead-b"]}
        onSuccess={onSuccess}
      />,
      { wrapper: createWrapper() },
    );

    await user.type(screen.getByLabelText(/nombre del segmento/i), "Mi segmento test");
    await user.click(screen.getByRole("button", { name: /crear segmento/i }));

    await waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({
          name: "Mi segmento test",
          segment_type: "STATIC",
          lead_ids: ["lead-a", "lead-b"],
        }),
      );
    });
  });

  it("shows validation error when name is empty", async () => {
    const user = userEvent.setup();

    render(
      <CreateSegmentDialog
        open
        onOpenChange={onOpenChange}
        selectedLeadIds={["lead-1"]}
        onSuccess={onSuccess}
      />,
      { wrapper: createWrapper() },
    );

    await user.click(screen.getByRole("button", { name: /crear segmento/i }));
    await waitFor(() => {
      expect(screen.getByText(/nombre es requerido/i)).toBeInTheDocument();
    });
  });

  it("calls onOpenChange(false) on cancel click", () => {
    render(
      <CreateSegmentDialog
        open
        onOpenChange={onOpenChange}
        selectedLeadIds={[]}
        onSuccess={onSuccess}
      />,
      { wrapper: createWrapper() },
    );

    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
