import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../../../api/copilot-api";
import { useCopilotStore } from "../../../store/copilot-store";
import { ProposalCard } from "../ProposalCard";

import type { ProposalUpdate } from "../../../store/copilot-store";
import type { FormRuntimeBridge } from "@/lib/form-runtime/copilot";
import type { SectionSchema } from "@/lib/form-runtime/schema/types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: () => Promise.resolve("test-token"),
  }),
}));

const sampleSchema: SectionSchema = {
  key: "brand.identity",
  label: "Brand Identity",
  fields: [
    {
      id: "identity.brand_name",
      label: "Brand name",
      path: "identity.brand_name",
      type: "string",
      hint: null,
    },
  ],
} as unknown as SectionSchema;

const sampleUpdates: ProposalUpdate[] = [
  {
    field_id: "identity.brand_name",
    new_value: "Visionarias",
    reason: "Cambio sugerido",
  },
];

function buildBridge(): FormRuntimeBridge {
  return {
    getSnapshot: () => ({
      sectionKey: "brand.identity",
      schema: sampleSchema,
      values: {},
      focusedField: null,
    }),
    patchField: vi.fn().mockResolvedValue(undefined),
    focusField: vi.fn(),
    subscribe: () => () => undefined,
  };
}

describe("ProposalCard B22-FP1", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      activeBridge: null,
      conversationId: "conv-fp1",
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("AC1: with bridge connected → patchField called + status applied", async () => {
    const bridge = buildBridge();
    useCopilotStore.setState({ activeBridge: bridge });

    render(<ProposalCard updates={sampleUpdates} messageId="msg-1" />);
    fireEvent.click(screen.getByRole("button", { name: /aplicar/i }));

    await waitFor(() => {
      expect(bridge.patchField).toHaveBeenCalledWith("identity.brand_name", "Visionarias");
      expect(screen.getByText("Aplicado")).toBeDefined();
    });
  });

  it("AC2: without bridge → fallback applyCopilotMutations call", async () => {
    const applySpy = vi.spyOn(api, "applyCopilotMutations").mockResolvedValue({
      applied: [
        {
          id: "mut-1",
          field_path: "identity.brand_name",
          domain: "brand",
          status: "applied",
        },
      ],
      rejected: [],
    });
    const eventSpy = vi.spyOn(api, "reportCopilotEvent").mockImplementation(() => undefined);

    render(<ProposalCard updates={sampleUpdates} messageId="msg-2" />);
    fireEvent.click(screen.getByRole("button", { name: /aplicar/i }));

    await waitFor(() => {
      expect(applySpy).toHaveBeenCalledWith(
        "conv-fp1",
        "msg-2",
        [
          {
            field_id: "identity.brand_name",
            new_value: "Visionarias",
            reason: "Cambio sugerido",
          },
        ],
        "test-token",
      );
      expect(screen.getByText("Aplicado")).toBeDefined();
    });

    // AC4: event payload includes mutation_ids and path=fallback
    const acceptedCall = eventSpy.mock.calls.find((call) => call[0] === "proposal_accepted");
    expect(acceptedCall).toBeDefined();
    expect(acceptedCall?.[1]).toEqual(
      expect.objectContaining({
        mutation_ids: ["mut-1"],
        path: "fallback",
      }),
    );
  });

  it("AC3: fallback throws → status failed + alert visible", async () => {
    vi.spyOn(api, "applyCopilotMutations").mockRejectedValue(
      new Error("apply_mutations_500: backend down"),
    );

    render(<ProposalCard updates={sampleUpdates} messageId="msg-3" />);
    fireEvent.click(screen.getByRole("button", { name: /aplicar/i }));

    await waitFor(() => {
      expect(screen.getByText("No se pudo aplicar")).toBeDefined();
      expect(screen.getByRole("alert")).toBeDefined();
    });
    expect(screen.queryByText("Aplicado")).toBeNull();
  });

  it("AC3: fallback returns rejected → status failed + reason rendered", async () => {
    vi.spyOn(api, "applyCopilotMutations").mockResolvedValue({
      applied: [],
      rejected: [
        {
          field_id: "identity.brand_name",
          reason: "campo no editable",
        },
      ],
    });

    render(<ProposalCard updates={sampleUpdates} messageId="msg-4" />);
    fireEvent.click(screen.getByRole("button", { name: /aplicar/i }));

    await waitFor(() => {
      expect(screen.getByText("campo no editable")).toBeDefined();
      expect(screen.getByText("No se pudo aplicar")).toBeDefined();
    });
  });

  it("AC3: failed status exposes Reintentar button", async () => {
    const applySpy = vi
      .spyOn(api, "applyCopilotMutations")
      .mockRejectedValueOnce(new Error("apply_mutations_500: oops"))
      .mockResolvedValueOnce({
        applied: [
          {
            id: "mut-retry",
            field_path: "identity.brand_name",
            domain: "brand",
            status: "applied",
          },
        ],
        rejected: [],
      });

    render(<ProposalCard updates={sampleUpdates} messageId="msg-5" />);
    fireEvent.click(screen.getByRole("button", { name: /aplicar/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /reintentar/i })).toBeDefined();
    });

    fireEvent.click(screen.getByRole("button", { name: /reintentar/i }));
    await waitFor(() => {
      expect(screen.getByText("Aplicado")).toBeDefined();
    });
    expect(applySpy).toHaveBeenCalledTimes(2);
  });
});
