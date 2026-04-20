import { describe, expect, it } from "vitest";

import { OFFER_SCHEMA_REGISTRY } from "../index";

import type { FieldSchema, SectionSchema } from "@/lib/form-runtime/schema";

/**
 * Quality ratchet — invariantes cross-schema que elevan el estándar de
 * los 22 schemas de Offer Studio.
 *
 * Estos tests son **ratchet-style**: una vez que pasan, cualquier cambio
 * futuro que los rompa falla CI. La única forma aceptada de desactivar
 * una regla es agregar un schema a la allowlist con justificación, y las
 * allowlists solo pueden encoger.
 *
 * Invariantes enforzadas:
 *
 * 1. **Cobertura de hint** — todo field no-custom tiene ``hint`` O
 *    ``placeholder`` no vacío. Un field sin pista es una pregunta a
 *    ciegas que el microempresario no sabe responder.
 * 2. **Labels sin jerga técnica** — ningún label usa palabras
 *    "specific_details", "path", "enum value" (filtrado conservador).
 * 3. **Paths únicos intra-schema** — no hay dos fields en el mismo
 *    schema escribiendo al mismo path (evita silent overwrites).
 * 4. **Enums con al menos 2 opciones** — un enum de 1 opción es un
 *    constant, usa ``boolean`` o ``text`` readonly.
 * 5. **Scope coherente** — si un schema declara ``scope: "mixed"``,
 *    todos sus fields deben declarar ``owner``. Si declara
 *    ``offer_level`` o ``edition_level``, los fields no deben declarar
 *    ``owner`` (la sección entera tiene un único dueño implícito).
 */

function collectFields(schema: SectionSchema): FieldSchema[] {
  return [...schema.fields];
}

describe("Schema quality ratchet — hint coverage", () => {
  it("every non-custom field declares a hint or placeholder", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      for (const field of collectFields(schema)) {
        if (field.type === "custom") continue;
        const hint = field.hint?.trim() ?? "";
        const placeholder = field.placeholder?.trim() ?? "";
        if (!hint && !placeholder) {
          violations.push(`${key}.${field.id} (${field.type})`);
        }
      }
    }
    expect(
      violations,
      `Every non-custom field must have a hint or placeholder — microempresarios Latam need guidance to fill them:\n${violations.join(
        "\n",
      )}`,
    ).toEqual([]);
  });
});

describe("Schema quality ratchet — no technical jargon in labels", () => {
  it("labels never leak internal concepts (path, specific_details, enum value)", () => {
    const jargonPatterns = [/specific_details/i, /enum value/i, /\bpath\b/i];
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      for (const field of collectFields(schema)) {
        for (const pattern of jargonPatterns) {
          if (pattern.test(field.label)) {
            violations.push(
              `${key}.${field.id} — label contains technical jargon: "${field.label}"`,
            );
            break;
          }
        }
      }
    }
    expect(
      violations,
      `Field labels must be in user-facing language:\n${violations.join("\n")}`,
    ).toEqual([]);
  });
});

describe("Schema quality ratchet — unique paths within a schema", () => {
  it("no two fields inside the same schema share the same path", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      const paths = schema.fields.map((f) => f.path);
      const seen = new Map<string, string>();
      for (const field of schema.fields) {
        const existing = seen.get(field.path);
        if (existing !== undefined) {
          violations.push(
            `${key} — duplicate path "${field.path}" between fields ${existing!} and ${field.id}`,
          );
        } else {
          seen.set(field.path, field.id);
        }
      }
      void paths;
    }
    expect(
      violations,
      `Duplicate paths silently overwrite each other at save time:\n${violations.join("\n")}`,
    ).toEqual([]);
  });
});

describe("Schema quality ratchet — enum sanity", () => {
  it("every enum field has at least 2 options", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      for (const field of collectFields(schema)) {
        if (field.type !== "enum") continue;
        const options = field.options ?? [];
        if (options.length < 2) {
          violations.push(`${key}.${field.id} has ${options.length} option(s)`);
        }
      }
    }
    expect(
      violations,
      `Enums with < 2 options should be booleans or read-only text:\n${violations.join("\n")}`,
    ).toEqual([]);
  });

  it("every enum option has a non-empty label", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      for (const field of collectFields(schema)) {
        if (field.type !== "enum") continue;
        for (const option of field.options ?? []) {
          if (!option.label.trim()) {
            violations.push(`${key}.${field.id} — option value "${option.value}" has empty label`);
          }
        }
      }
    }
    expect(violations, `Enum options must render something:\n${violations.join("\n")}`).toEqual([]);
  });
});

describe("Schema quality ratchet — scope/owner coherence", () => {
  it("MIXED-scope schemas declare owner on every field", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      if (schema.scope !== "mixed") continue;
      for (const field of collectFields(schema)) {
        if (!field.owner) {
          violations.push(`${key}.${field.id} — missing owner in a mixed-scope schema`);
        }
      }
    }
    expect(
      violations,
      `Every field in a mixed-scope schema must declare owner: 'offer' | 'edition':\n${violations.join(
        "\n",
      )}`,
    ).toEqual([]);
  });

  it("single-owner schemas (offer_level / edition_level) do not declare per-field owner", () => {
    const violations: string[] = [];
    for (const [key, schema] of Object.entries(OFFER_SCHEMA_REGISTRY)) {
      if (schema.scope === "mixed" || schema.scope === undefined) continue;
      for (const field of collectFields(schema)) {
        if (field.owner) {
          violations.push(
            `${key}.${field.id} — redundant owner "${field.owner}" in a ${schema.scope} schema`,
          );
        }
      }
    }
    expect(
      violations,
      `offer_level / edition_level schemas imply owner — do not declare it per field:\n${violations.join(
        "\n",
      )}`,
    ).toEqual([]);
  });
});
