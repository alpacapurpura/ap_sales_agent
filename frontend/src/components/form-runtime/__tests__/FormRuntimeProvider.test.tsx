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
