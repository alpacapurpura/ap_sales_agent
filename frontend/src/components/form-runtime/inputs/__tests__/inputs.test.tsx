import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { registerAction, clearRegistry, type ActionComponent } from "@/lib/form-runtime/actions";

import { BooleanInput } from "../BooleanInput";
import { CustomInput } from "../CustomInput";
import { EmailInput } from "../EmailInput";
import { EnumInput } from "../EnumInput";
import { NumberInput } from "../NumberInput";
import { TextareaInput } from "../TextareaInput";
import { TextInput } from "../TextInput";
import { UrlInput } from "../UrlInput";

import type { FieldSchema } from "@/lib/form-runtime/schema";

function textField(overrides: Partial<FieldSchema> = {}): FieldSchema {
  return { id: "name", label: "Name", type: "text", path: "name", ...overrides };
}

describe("TextInput", () => {
  it("renders value and fires onChange on typing", () => {
    const onChange = vi.fn();
    render(<TextInput field={textField()} value="hello" onChange={onChange} />);
    const input = screen.getByDisplayValue("hello") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "world" } });
    expect(onChange).toHaveBeenCalledWith("world");
  });

  it("renders placeholder from schema", () => {
    render(
      <TextInput
        field={textField({ placeholder: "Ej: Visionarias" })}
        value=""
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByPlaceholderText("Ej: Visionarias")).toBeTruthy();
  });
});

describe("TextareaInput", () => {
  it("renders the value and emits onChange (auto-resize via react-textarea-autosize)", () => {
    const onChange = vi.fn();
    render(
      <TextareaInput
        field={textField({ type: "textarea", rows: 5 })}
        value="body"
        onChange={onChange}
      />,
    );
    const ta = screen.getByDisplayValue("body");
    expect(ta.tagName).toBe("TEXTAREA");
    expect(ta.className).toContain("resize-none");
    expect(ta.className).toContain("overflow-hidden");
  });
});

describe("TextareaInput storeAs newline_array", () => {
  function arrayField(overrides: Partial<FieldSchema> = {}): FieldSchema {
    return {
      id: "measurable_outcomes",
      label: "Resultados medibles",
      type: "textarea",
      path: "measurable_outcomes",
      storeAs: "newline_array",
      ...overrides,
    };
  }

  it("renders string[] as newline-joined string", () => {
    const { container } = render(
      <TextareaInput field={arrayField()} value={["a", "b"]} onChange={vi.fn()} />,
    );
    const ta = container.querySelector("textarea");
    expect(ta?.value).toBe("a\nb");
  });

  it("renders null as empty string (so placeholder shows)", () => {
    const { container } = render(
      <TextareaInput
        field={arrayField({ placeholder: "Escribe aquí" })}
        value={null}
        onChange={vi.fn()}
      />,
    );
    const ta = container.querySelector("textarea");
    expect(ta?.value).toBe("");
  });

  it("splits user input into string[] on onChange", () => {
    const onChange = vi.fn();
    render(
      <TextareaInput field={arrayField()} value={[]} onChange={onChange} />,
    );
    const ta = screen.getByRole("textbox");
    fireEvent.change(ta, { target: { value: "a\nb\nc" } });
    expect(onChange).toHaveBeenCalledWith(["a", "b", "c"]);
  });

  it("strips bullet prefixes when splitting (• - *)", () => {
    const onChange = vi.fn();
    render(
      <TextareaInput field={arrayField()} value={[]} onChange={onChange} />,
    );
    const ta = screen.getByRole("textbox");
    fireEvent.change(ta, { target: { value: "• foo\n- bar\n* baz" } });
    expect(onChange).toHaveBeenCalledWith(["foo", "bar", "baz"]);
  });

  it("filters empty lines when splitting", () => {
    const onChange = vi.fn();
    render(
      <TextareaInput field={arrayField()} value={[]} onChange={onChange} />,
    );
    const ta = screen.getByRole("textbox");
    fireEvent.change(ta, { target: { value: "foo\n\nbar\n" } });
    expect(onChange).toHaveBeenCalledWith(["foo", "bar"]);
  });

  it("plain mode (no storeAs) still passes string through unchanged", () => {
    const onChange = vi.fn();
    render(
      <TextareaInput
        field={textField({ type: "textarea" })}
        value="hello"
        onChange={onChange}
      />,
    );
    const ta = screen.getByDisplayValue("hello");
    fireEvent.change(ta, { target: { value: "world" } });
    expect(onChange).toHaveBeenCalledWith("world");
  });
});

describe("NumberInput", () => {
  it("emits null when cleared", () => {
    const onChange = vi.fn();
    render(<NumberInput field={textField({ type: "number" })} value={3} onChange={onChange} />);
    const input = screen.getByDisplayValue("3");
    fireEvent.change(input, { target: { value: "" } });
    expect(onChange).toHaveBeenCalledWith(null);
  });

  it("emits a number when changed", () => {
    const onChange = vi.fn();
    render(<NumberInput field={textField({ type: "number" })} value={null} onChange={onChange} />);
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "42" } });
    expect(onChange).toHaveBeenCalledWith(42);
  });
});

describe("BooleanInput", () => {
  it("flips on checked change", () => {
    const onChange = vi.fn();
    render(
      <BooleanInput field={textField({ type: "boolean" })} value={false} onChange={onChange} />,
    );
    fireEvent.click(screen.getByRole("switch"));
    expect(onChange).toHaveBeenCalledWith(true);
  });
});

describe("EnumInput", () => {
  it("renders the placeholder when value is empty", () => {
    render(
      <EnumInput
        field={textField({
          type: "enum",
          options: [{ value: "a", label: "A" }],
          placeholder: "Choose",
        })}
        value=""
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Choose")).toBeTruthy();
  });
});

describe("UrlInput", () => {
  it("has inputMode=url and a default placeholder", () => {
    render(<UrlInput field={textField({ type: "url" })} value="" onChange={vi.fn()} />);
    const input = screen.getByPlaceholderText("https://...") as HTMLInputElement;
    expect(input.type).toBe("url");
    expect(input.inputMode).toBe("url");
  });
});

describe("EmailInput", () => {
  it("has inputMode=email", () => {
    render(<EmailInput field={textField({ type: "email" })} value="a@b.co" onChange={vi.fn()} />);
    const input = screen.getByDisplayValue("a@b.co") as HTMLInputElement;
    expect(input.type).toBe("email");
  });
});

describe("CustomInput", () => {
  beforeEach(() => {
    clearRegistry();
  });

  it("renders placeholder when action is not registered", () => {
    render(
      <CustomInput
        field={textField({ type: "custom", action: "voice-clone" })}
        value=""
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/pendiente de registrar/i)).toBeTruthy();
  });

  it("renders the registered action component", () => {
    const Stub: ActionComponent<string> = ({ value }) => <div data-testid="stub">{value}</div>;
    registerAction("voice-clone", Stub as ActionComponent);
    render(
      <CustomInput
        field={textField({ type: "custom", action: "voice-clone" })}
        value="Hello"
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByTestId("stub").textContent).toBe("Hello");
  });

  it("renders error UI when schema is missing action key", () => {
    render(<CustomInput field={textField({ type: "custom" })} value="" onChange={vi.fn()} />);
    expect(screen.getByText(/Schema error/i)).toBeTruthy();
  });
});
