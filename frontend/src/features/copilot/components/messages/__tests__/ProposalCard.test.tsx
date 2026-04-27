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
    // Default to "no journal entries yet" so existing tests render with
    // every field pending. Individual tests below override this when
    // they need to assert rehydrate behaviour.
    vi.spyOn(api, "fetchAppliedMutations").mockResolvedValue([]);
    // Default to a no-op apply call so tests that only exercise the
    // bridge path don't hit real ``fetch`` from the journal echo.
    // Individual tests override this spy when they assert FE→BE wire.
    vi.spyOn(api, "applyCopilotMutations").mockResolvedValue({
      applied: [],
      rejected: [],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("AC1: with bridge connected → patchField called + status applied", async () => {
    const bridge = buildBridge();
    useCopilotStore.setState({ activeBridge: bridge });

    render(<ProposalCard updates={sampleUpdates} messageId="msg-1" />);
    fireEvent.click(screen.getByRole("button", { name: /aceptar/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /aceptar/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /aceptar/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /aceptar/i }));

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
    fireEvent.click(screen.getByRole("button", { name: /aceptar/i }));

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

// Sprint 1 — collapsable + per-field + batch (Opción C UX)
const tenUpdates: ProposalUpdate[] = Array.from({ length: 10 }, (_, i) => ({
  field_id: `psychographics.field_${i}`,
  new_value: `valor ${i}`,
  reason: `razón ${i}`,
}));

const tenSchema: SectionSchema = {
  key: "brand.buyer-persona",
  label: "Buyer Persona",
  fields: tenUpdates.map((u) => ({
    id: u.field_id,
    label: u.field_id,
    path: u.field_id,
    type: "string",
    hint: null,
  })),
} as unknown as SectionSchema;

function buildBuyerBridge(): FormRuntimeBridge {
  return {
    getSnapshot: () => ({
      sectionKey: "brand.buyer-persona",
      schema: tenSchema,
      values: {},
      focusedField: null,
    }),
    patchField: vi.fn().mockResolvedValue(undefined),
    focusField: vi.fn(),
    subscribe: () => () => undefined,
  };
}

describe("ProposalCard Sprint 1 — collapsable + per-field + batch", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      activeBridge: null,
      conversationId: "conv-sprint1",
    });
    vi.spyOn(api, "fetchAppliedMutations").mockResolvedValue([]);
    // Default to a no-op apply call so tests that only exercise the
    // bridge path don't hit real ``fetch`` from the journal echo.
    // Individual tests override this spy when they assert FE→BE wire.
    vi.spyOn(api, "applyCopilotMutations").mockResolvedValue({
      applied: [],
      rejected: [],
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("collapsed by default when N>=2 → header shows count + Ver detalles toggle", () => {
    render(<ProposalCard updates={tenUpdates} messageId="m-c1" />);

    expect(screen.getByText(/10\s+campos/i)).toBeDefined();
    expect(screen.getByRole("button", { name: /ver detalles/i })).toBeDefined();
    // Per-row content should NOT be visible when collapsed.
    expect(screen.queryByText("psychographics.field_0")).toBeNull();
  });

  it("expand toggle reveals per-field rows with individual Aceptar/Rechazar", () => {
    render(<ProposalCard updates={tenUpdates} messageId="m-c2" />);
    fireEvent.click(screen.getByRole("button", { name: /ver detalles/i }));

    expect(screen.getByText("psychographics.field_0")).toBeDefined();
    expect(screen.getByText("psychographics.field_9")).toBeDefined();
    // Each row exposes per-field accept + reject affordances.
    const acceptButtons = screen.getAllByRole("button", { name: /^aceptar$/i });
    const rejectButtons = screen.getAllByRole("button", { name: /^rechazar$/i });
    expect(acceptButtons.length).toBe(10);
    expect(rejectButtons.length).toBe(10);
  });

  it("Aceptar todos with bridge → patchField called once per update", async () => {
    const bridge = buildBuyerBridge();
    useCopilotStore.setState({ activeBridge: bridge });

    render(<ProposalCard updates={tenUpdates} messageId="m-c3" />);
    fireEvent.click(screen.getByRole("button", { name: /aceptar todos/i }));

    await waitFor(() => {
      expect(bridge.patchField).toHaveBeenCalledTimes(10);
      expect(screen.getByText(/aplicado/i)).toBeDefined();
    });
  });

  it("per-field Aceptar applies one only — others stay pending", async () => {
    const bridge = buildBuyerBridge();
    useCopilotStore.setState({ activeBridge: bridge });

    render(<ProposalCard updates={tenUpdates} messageId="m-c4" />);
    fireEvent.click(screen.getByRole("button", { name: /ver detalles/i }));
    const acceptButtons = screen.getAllByRole("button", { name: /^aceptar$/i });
    fireEvent.click(acceptButtons[0]);

    await waitFor(() => {
      expect(bridge.patchField).toHaveBeenCalledTimes(1);
      expect(bridge.patchField).toHaveBeenCalledWith("psychographics.field_0", "valor 0");
    });
    // Footer "Aceptar todos" remains visible; pending count drops to 9.
    expect(screen.getByRole("button", { name: /aceptar todos/i })).toBeDefined();
  });

  it("Rechazar todos emits proposal_rejected_batch event without bridge calls", async () => {
    const bridge = buildBuyerBridge();
    useCopilotStore.setState({ activeBridge: bridge });
    const eventSpy = vi.spyOn(api, "reportCopilotEvent").mockImplementation(() => undefined);

    render(<ProposalCard updates={tenUpdates} messageId="m-c5" />);
    fireEvent.click(screen.getByRole("button", { name: /rechazar todos/i }));

    await waitFor(() => {
      const rejectedCall = eventSpy.mock.calls.find(
        (call) => call[0] === "proposal_rejected_batch",
      );
      expect(rejectedCall).toBeDefined();
      expect(rejectedCall?.[1]).toEqual(expect.objectContaining({ field_count: 10 }));
    });
    expect(bridge.patchField).not.toHaveBeenCalled();
  });

  it("rehydrates applied state from the mutation journal on mount", async () => {
    vi.spyOn(api, "fetchAppliedMutations").mockResolvedValue([
      {
        id: "mut-r1",
        message_id: "m-rehydrate",
        domain: "buyer_persona",
        entity_id: null,
        field_path: "psychographics.field_0",
        applied_at: "2026-04-27T21:01:00Z",
      },
      {
        id: "mut-r2",
        message_id: "m-rehydrate",
        domain: "buyer_persona",
        entity_id: null,
        field_path: "psychographics.field_3",
        applied_at: "2026-04-27T21:01:01Z",
      },
    ]);

    render(<ProposalCard updates={tenUpdates} messageId="m-rehydrate" />);
    fireEvent.click(screen.getByRole("button", { name: /ver detalles/i }));

    // Two journaled fields should render the green ``Aplicado`` chip; the
    // remaining eight stay actionable.
    await waitFor(() => {
      expect(screen.getAllByText(/^aplicado$/i).length).toBe(2);
    });
    const acceptButtons = screen.getAllByRole("button", { name: /^aceptar$/i });
    expect(acceptButtons.length).toBe(8);
  });

  it("Aceptar todos with bridge → echoes journal once per applied field", async () => {
    const bridge = buildBuyerBridge();
    useCopilotStore.setState({ activeBridge: bridge });
    const applySpy = vi.spyOn(api, "applyCopilotMutations").mockResolvedValue({
      applied: [],
      rejected: [],
    });

    render(<ProposalCard updates={tenUpdates} messageId="m-echo" />);
    fireEvent.click(screen.getByRole("button", { name: /aceptar todos/i }));

    await waitFor(() => {
      expect(bridge.patchField).toHaveBeenCalledTimes(10);
      expect(applySpy).toHaveBeenCalledTimes(10);
    });
    // Each echo carries exactly one update — the journal write is per
    // field so the natural-key idempotency guard is exercised once per
    // accepted row.
    for (const [, , updates] of applySpy.mock.calls) {
      expect(updates).toHaveLength(1);
    }
  });

  it("per-field Rechazar marks only that row + others applyable via Aceptar todos", async () => {
    const bridge = buildBuyerBridge();
    useCopilotStore.setState({ activeBridge: bridge });

    render(<ProposalCard updates={tenUpdates} messageId="m-c6" />);
    fireEvent.click(screen.getByRole("button", { name: /ver detalles/i }));
    const rejectButtons = screen.getAllByRole("button", { name: /^rechazar$/i });
    fireEvent.click(rejectButtons[0]);

    fireEvent.click(screen.getByRole("button", { name: /aceptar todos/i }));

    await waitFor(() => {
      // 10 - 1 rejected = 9 patches.
      expect(bridge.patchField).toHaveBeenCalledTimes(9);
    });
  });
});
