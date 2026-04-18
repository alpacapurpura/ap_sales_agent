import { describe, it, expect } from "vitest";

import { parseSectionSchema, SchemaParseError } from "../parser";

import type { SectionSchema } from "../types";

function makeSchema(overrides: Partial<SectionSchema> = {}): SectionSchema {
  return {
    key: "brand.identity",
    title: "Identity",
    fields: [{ id: "name", label: "Name", type: "text", path: "name" }],
    ...overrides,
  };
}

describe("parseSectionSchema", () => {
  it("accepts a minimal well-formed schema", () => {
    const schema = makeSchema();
    expect(() => parseSectionSchema(schema)).not.toThrow();
    expect(parseSectionSchema(schema)).toEqual(schema);
  });

  it("accepts every FieldType with its minimum required props", () => {
    const schema = makeSchema({
      fields: [
        { id: "t", label: "t", type: "text", path: "t" },
        { id: "ta", label: "ta", type: "textarea", path: "ta", rows: 3 },
        {
          id: "en",
          label: "en",
          type: "enum",
          path: "en",
          options: [{ value: "a", label: "A" }],
        },
        { id: "n", label: "n", type: "number", path: "n" },
        { id: "b", label: "b", type: "boolean", path: "b" },
        { id: "u", label: "u", type: "url", path: "u" },
        { id: "e", label: "e", type: "email", path: "e" },
        {
          id: "a",
          label: "a",
          type: "array",
          path: "a",
          itemSchema: {
            fields: [{ id: "nested", label: "Nested", type: "text", path: "nested" }],
          },
        },
        { id: "c", label: "c", type: "custom", path: "c", action: "voice-clone" },
      ],
    });
    expect(() => parseSectionSchema(schema)).not.toThrow();
  });

  it("rejects missing section key", () => {
    expect(() => parseSectionSchema(makeSchema({ key: "" }))).toThrow(SchemaParseError);
  });

  it("rejects missing section title", () => {
    expect(() => parseSectionSchema(makeSchema({ title: "" }))).toThrow(SchemaParseError);
  });

  it("rejects empty fields array", () => {
    expect(() => parseSectionSchema(makeSchema({ fields: [] }))).toThrow(/at least one field/i);
  });

  it("rejects duplicate field ids within a section", () => {
    const schema = makeSchema({
      fields: [
        { id: "dup", label: "A", type: "text", path: "a" },
        { id: "dup", label: "B", type: "text", path: "b" },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/duplicate.*id/i);
  });

  it("rejects field with missing id", () => {
    const schema = makeSchema({
      fields: [{ id: "", label: "A", type: "text", path: "a" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/id/i);
  });

  it("rejects field with missing path", () => {
    const schema = makeSchema({
      fields: [{ id: "a", label: "A", type: "text", path: "" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/path/i);
  });

  it("rejects unknown field type", () => {
    const schema = makeSchema({
      fields: [
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { id: "a", label: "A", type: "invalid" as any, path: "a" },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/type/i);
  });

  it("rejects enum field without options", () => {
    const schema = makeSchema({
      fields: [{ id: "a", label: "A", type: "enum", path: "a" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/enum.*options/i);
  });

  it("rejects enum field with empty options", () => {
    const schema = makeSchema({
      fields: [{ id: "a", label: "A", type: "enum", path: "a", options: [] }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/options/i);
  });

  it("rejects array field without itemSchema", () => {
    const schema = makeSchema({
      fields: [{ id: "a", label: "A", type: "array", path: "a" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/array.*itemSchema/i);
  });

  it("rejects custom field without action key", () => {
    const schema = makeSchema({
      fields: [{ id: "a", label: "A", type: "custom", path: "a" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/custom.*action/i);
  });

  it("recursively validates nested array itemSchema fields", () => {
    const schema = makeSchema({
      fields: [
        {
          id: "members",
          label: "Members",
          type: "array",
          path: "members",
          itemSchema: {
            fields: [
              { id: "dup", label: "X", type: "text", path: "x" },
              { id: "dup", label: "Y", type: "text", path: "y" },
            ],
          },
        },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/duplicate.*id/i);
  });

  it("accepts valid per-field saveMode override", () => {
    const schema = makeSchema({
      fields: [{ id: "name", label: "Name", type: "text", path: "name", saveMode: "explicit" }],
    });
    expect(() => parseSectionSchema(schema)).not.toThrow();
  });

  it("rejects invalid per-field saveMode", () => {
    const schema = makeSchema({
      fields: [
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { id: "name", label: "Name", type: "text", path: "name", saveMode: "bogus" as any },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/saveMode/i);
  });

  it("exposes a human-readable error message with field id in context", () => {
    const schema = makeSchema({
      fields: [{ id: "dup", label: "A", type: "custom", path: "a" }],
    });
    try {
      parseSectionSchema(schema);
    } catch (err) {
      expect(err).toBeInstanceOf(SchemaParseError);
      expect((err as SchemaParseError).message).toContain("dup");
      return;
    }
    throw new Error("parser did not throw");
  });
});

describe("parseSectionSchema: offer/edition scope + owner (Sprint 6)", () => {
  it("accepts a section without scope declared (legacy single-owner)", () => {
    expect(() => parseSectionSchema(makeSchema())).not.toThrow();
  });

  it("accepts offer_level + fields without owner (owner is implicit)", () => {
    const schema = makeSchema({
      scope: "offer_level",
      fields: [{ id: "name", label: "Name", type: "text", path: "name" }],
    });
    expect(() => parseSectionSchema(schema)).not.toThrow();
  });

  it("accepts edition_level + fields declaring owner='edition'", () => {
    const schema = makeSchema({
      scope: "edition_level",
      fields: [
        { id: "start", label: "Inicio", type: "text", path: "start_date", owner: "edition" },
      ],
    });
    expect(() => parseSectionSchema(schema)).not.toThrow();
  });

  it("rejects offer_level fields declaring owner='edition'", () => {
    const schema = makeSchema({
      scope: "offer_level",
      fields: [{ id: "x", label: "X", type: "text", path: "x", owner: "edition" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(
      /section scope "offer_level" expects owner="offer"/,
    );
  });

  it("rejects edition_level fields declaring owner='offer'", () => {
    const schema = makeSchema({
      scope: "edition_level",
      fields: [{ id: "x", label: "X", type: "text", path: "x", owner: "offer" }],
    });
    expect(() => parseSectionSchema(schema)).toThrow(
      /section scope "edition_level" expects owner="edition"/,
    );
  });

  it("accepts mixed + every field declaring owner", () => {
    const schema = makeSchema({
      scope: "mixed",
      fields: [
        { id: "a", label: "A", type: "text", path: "a", owner: "offer" },
        { id: "b", label: "B", type: "text", path: "b", owner: "edition" },
      ],
    });
    expect(() => parseSectionSchema(schema)).not.toThrow();
  });

  it("rejects mixed when any field omits owner", () => {
    const schema = makeSchema({
      scope: "mixed",
      fields: [
        { id: "a", label: "A", type: "text", path: "a", owner: "offer" },
        { id: "b", label: "B", type: "text", path: "b" },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/mixed scope requires every field.*owner/);
  });

  it("rejects invalid schema.scope values", () => {
    const schema = makeSchema({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      scope: "bogus" as any,
    });
    expect(() => parseSectionSchema(schema)).toThrow(/invalid schema.scope/);
  });

  it("rejects invalid field.owner values", () => {
    const schema = makeSchema({
      fields: [
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        { id: "x", label: "X", type: "text", path: "x", owner: "bogus" as any },
      ],
    });
    expect(() => parseSectionSchema(schema)).toThrow(/invalid field.owner/);
  });
});
