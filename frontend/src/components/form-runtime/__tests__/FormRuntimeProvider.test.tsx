import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { EditableField } from "../EditableField";
import { useFormRuntime } from "../FormRuntimeContext";
import { FormRuntimeProvider } from "../FormRuntimeProvider";

import type { SectionSchema } from "@/lib/form-runtime/schema";

const SCHEMA: SectionSchema = {
  key: "brand.identity",
  title: "Identity",
  fields: [
    { id: "name", label: "Name", type: "text", path: "name" },
    { id: "tagline", label: "Tagline", type: "text", path: "tagline" },
  ],
};

async function flushMicrotasks(): Promise<void> {
  for (let i = 0; i < 3; i += 1) {
    await Promise.resolve();
  }
}

function ProbeDirty() {
  const { isDirty, undoSession } = useFormRuntime();
  return (
    <div>
      <span data-testid="dirty">{isDirty ? "dirty" : "clean"}</span>
      <button type="button" onClick={undoSession} data-testid="undo">
        undo
      </button>
    </div>
  );
}

describe("FormRuntimeProvider", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("exposes initial values through context", () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider
        schema={SCHEMA}
        initialValues={{ name: "Visionarias", tagline: "" }}
        onSave={onSave}
      >
        <EditableField field={SCHEMA.fields[0]} />
      </FormRuntimeProvider>,
    );
    expect(screen.getByDisplayValue("Visionarias")).toBeTruthy();
  });

  it("composes full values and triggers autosave after debounce", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider
        schema={SCHEMA}
        initialValues={{ name: "old", tagline: "line" }}
        onSave={onSave}
      >
        <EditableField field={SCHEMA.fields[0]} />
      </FormRuntimeProvider>,
    );

    const input = screen.getByDisplayValue("old");
    act(() => {
      fireEvent.change(input, { target: { value: "new" } });
    });

    await act(async () => {
      vi.advanceTimersByTime(900);
      await flushMicrotasks();
    });

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith({ name: "new", tagline: "line" });
  });

  it("marks isDirty on field change and restores via undoSession", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider
        schema={SCHEMA}
        initialValues={{ name: "start", tagline: "" }}
        onSave={onSave}
      >
        <EditableField field={SCHEMA.fields[0]} />
        <ProbeDirty />
      </FormRuntimeProvider>,
    );

    expect(screen.getByTestId("dirty").textContent).toBe("clean");

    const input = screen.getByDisplayValue("start");
    act(() => {
      fireEvent.change(input, { target: { value: "changed" } });
    });
    expect(screen.getByTestId("dirty").textContent).toBe("dirty");

    act(() => {
      screen.getByTestId("undo").click();
    });
    expect(screen.getByDisplayValue("start")).toBeTruthy();
    expect(screen.getByTestId("dirty").textContent).toBe("clean");
  });

  it("does not fire onSave when saveMode is explicit", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider
        schema={SCHEMA}
        initialValues={{ name: "a", tagline: "" }}
        onSave={onSave}
        saveMode="explicit"
      >
        <EditableField field={SCHEMA.fields[0]} />
      </FormRuntimeProvider>,
    );

    const input = screen.getByDisplayValue("a");
    act(() => {
      fireEvent.change(input, { target: { value: "b" } });
    });
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await flushMicrotasks();
    });

    expect(onSave).not.toHaveBeenCalled();
  });
});

describe("useFormRuntime", () => {
  it("throws outside a provider", () => {
    const spy = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => render(<ProbeDirty />)).toThrow(/FormRuntimeProvider/);
    spy.mockRestore();
  });
});

// Nested path round-trip — locks the contract for schemas that mirror JSONB
// sub-key shapes (buyer_persona demographics.* / psychographics.* /
// buyer_journey.*). A regression here re-introduces the silent data loss
// where the provider used to write a literal ``"a.b"`` flat key instead
// of nesting into ``a.b`` (conv 0d64c4a9, 2026-04-27).
const NESTED_SCHEMA: SectionSchema = {
  key: "brand.buyer-persona",
  title: "Buyer persona",
  fields: [
    { id: "name", label: "Nombre", type: "text", path: "name" },
    { id: "age_range", label: "Rango etario", type: "text", path: "demographics.age_range" },
    { id: "occupation", label: "Ocupación", type: "text", path: "demographics.occupation" },
  ],
};

interface BuyerLike {
  name?: string;
  demographics?: { age_range?: string; occupation?: string; location?: string };
  pain_points?: unknown[];
}

function ProbeValues() {
  const { values } = useFormRuntime();
  return <pre data-testid="values">{JSON.stringify(values)}</pre>;
}

describe("FormRuntimeProvider · nested paths", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("EditableField reads a dotted path through getNestedPath", () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider<BuyerLike>
        schema={NESTED_SCHEMA}
        initialValues={{
          demographics: { age_range: "30-42", location: "Lima" },
        }}
        onSave={onSave}
        saveMode="explicit"
      >
        <EditableField field={NESTED_SCHEMA.fields[1]} />
      </FormRuntimeProvider>,
    );
    expect(screen.getByDisplayValue("30-42")).toBeTruthy();
  });

  it("typing into a dotted-path field nests into the parent object on autosave", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider<BuyerLike>
        schema={NESTED_SCHEMA}
        initialValues={{
          name: "Valeria",
          demographics: { location: "Lima" },
          pain_points: [{ description: "x", severity: 4 }],
        }}
        onSave={onSave}
      >
        <EditableField field={NESTED_SCHEMA.fields[1]} />
      </FormRuntimeProvider>,
    );

    const input = screen.getByLabelText("Rango etario");
    act(() => {
      fireEvent.change(input, { target: { value: "30-42" } });
    });
    await act(async () => {
      vi.advanceTimersByTime(900);
      await flushMicrotasks();
    });

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith({
      name: "Valeria",
      demographics: { location: "Lima", age_range: "30-42" },
      pain_points: [{ description: "x", severity: 4 }],
    });
  });

  it("never produces a literal flat key for dotted paths", () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(
      <FormRuntimeProvider<BuyerLike>
        schema={NESTED_SCHEMA}
        initialValues={{ demographics: {} }}
        onSave={onSave}
        saveMode="explicit"
      >
        <EditableField field={NESTED_SCHEMA.fields[2]} />
        <ProbeValues />
      </FormRuntimeProvider>,
    );
    const input = screen.getByLabelText("Ocupación");
    act(() => {
      fireEvent.change(input, { target: { value: "Fundadora" } });
    });
    const dump = JSON.parse(screen.getByTestId("values").textContent || "{}") as Record<
      string,
      unknown
    >;
    expect(dump).toMatchObject({ demographics: { occupation: "Fundadora" } });
    expect(dump["demographics.occupation"]).toBeUndefined();
  });
});
