/**
 * Runtime validator for SectionSchema. Catches authoring errors at module load
 * so broken schemas never reach the renderer. Throws SchemaParseError with a
 * human-readable message pointing at the offending field id.
 */

import type {
  FieldLayout,
  FieldOwner,
  FieldSchema,
  FieldType,
  ItemSchema,
  SaveMode,
  SectionKind,
  SectionScope,
  SectionSchema,
} from "./types";

/** Raised when a schema fails structural validation. */
export class SchemaParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SchemaParseError";
  }
}

const VALID_FIELD_TYPES: ReadonlySet<FieldType> = new Set<FieldType>([
  "text",
  "textarea",
  "enum",
  "number",
  "boolean",
  "url",
  "email",
  "array",
  "custom",
]);

const VALID_SAVE_MODES: ReadonlySet<SaveMode> = new Set<SaveMode>([
  "explicit",
  "autosave",
  "autosave-with-banner",
]);

const VALID_SECTION_SCOPES: ReadonlySet<SectionScope> = new Set<SectionScope>([
  "offer_level",
  "edition_level",
  "mixed",
]);

const VALID_FIELD_OWNERS: ReadonlySet<FieldOwner> = new Set<FieldOwner>(["offer", "edition"]);

const VALID_FIELD_LAYOUTS: ReadonlySet<FieldLayout> = new Set<FieldLayout>([
  "full",
  "half",
  "two-thirds",
]);

const VALID_SECTION_KINDS: ReadonlySet<SectionKind> = new Set<SectionKind>([
  "singleton",
  "collection",
]);

function assertBaseFieldShape(field: FieldSchema, loc: string): void {
  if (!field.id || typeof field.id !== "string") {
    throw new SchemaParseError(`${loc}: field.id is required and must be a non-empty string`);
  }
  if (!field.label || typeof field.label !== "string") {
    throw new SchemaParseError(`${loc}: field.label is required`);
  }
  if (!field.path || typeof field.path !== "string") {
    throw new SchemaParseError(`${loc}: field.path is required`);
  }
  if (!VALID_FIELD_TYPES.has(field.type)) {
    throw new SchemaParseError(`${loc}: unknown field.type "${field.type}"`);
  }
  if (field.saveMode !== undefined && !VALID_SAVE_MODES.has(field.saveMode)) {
    throw new SchemaParseError(`${loc}: invalid field.saveMode "${field.saveMode}"`);
  }
  if (field.owner !== undefined && !VALID_FIELD_OWNERS.has(field.owner)) {
    throw new SchemaParseError(`${loc}: invalid field.owner "${field.owner}"`);
  }
  if (field.layout !== undefined && !VALID_FIELD_LAYOUTS.has(field.layout)) {
    throw new SchemaParseError(`${loc}: invalid field.layout "${field.layout}"`);
  }
}

/**
 * Enforces the offer/edition scope invariants — every field in a ``mixed``
 * section must declare ``owner``; fields in single-owner sections must
 * either omit ``owner`` or match the section scope. This guards at load
 * time so a page cannot mount a schema where the runtime would not know
 * where to dispatch a save.
 */
function validateScopeOwnership(schema: SectionSchema, context: string): void {
  const { scope } = schema;
  if (scope === undefined) return;

  if (scope === "mixed") {
    const unowned = schema.fields.filter((f) => f.owner === undefined);
    if (unowned.length > 0) {
      const ids = unowned.map((f) => `"${f.id}"`).join(", ");
      throw new SchemaParseError(
        `${context}: mixed scope requires every field to declare owner; missing on ${ids}`,
      );
    }
    return;
  }

  const expectedOwner: FieldOwner = scope === "offer_level" ? "offer" : "edition";
  const mismatched = schema.fields.filter(
    (f) => f.owner !== undefined && f.owner !== expectedOwner,
  );
  if (mismatched.length > 0) {
    const ids = mismatched.map((f) => `"${f.id}" (owner="${f.owner}")`).join(", ");
    throw new SchemaParseError(
      `${context}: section scope "${scope}" expects owner="${expectedOwner}"; mismatched fields ${ids}`,
    );
  }
}

function validateEnumField(field: FieldSchema, loc: string): void {
  if (!field.options || field.options.length === 0) {
    throw new SchemaParseError(`${loc}: enum field requires non-empty options array`);
  }
  for (const option of field.options) {
    if (!option || typeof option.value !== "string" || typeof option.label !== "string") {
      throw new SchemaParseError(`${loc}: enum option requires string value + label`);
    }
  }
}

function validateArrayField(field: FieldSchema, loc: string): void {
  if (!field.itemSchema) {
    throw new SchemaParseError(`${loc}: array field requires itemSchema`);
  }
  validateItemSchema(field.itemSchema, `${loc}.itemSchema`);
}

function validateCustomField(field: FieldSchema, loc: string): void {
  if (!field.action || typeof field.action !== "string") {
    throw new SchemaParseError(`${loc}: custom field requires action (registry key)`);
  }
}

const PER_TYPE_VALIDATORS: Partial<Record<FieldType, (f: FieldSchema, loc: string) => void>> = {
  enum: validateEnumField,
  array: validateArrayField,
  custom: validateCustomField,
};

function validateField(field: FieldSchema, context: string): void {
  const loc = `${context} [id="${field.id || "?"}"]`;
  assertBaseFieldShape(field, loc);
  PER_TYPE_VALIDATORS[field.type]?.(field, loc);
}

function validateItemSchema(item: ItemSchema, context: string): void {
  if (!Array.isArray(item.fields) || item.fields.length === 0) {
    throw new SchemaParseError(`${context}: itemSchema must declare at least one field`);
  }
  assertUniqueIds(item.fields, context);
  for (const field of item.fields) {
    validateField(field, context);
  }
}

function assertUniqueIds(fields: FieldSchema[], context: string): void {
  const seen = new Set<string>();
  for (const field of fields) {
    if (field.id && seen.has(field.id)) {
      throw new SchemaParseError(`${context}: duplicate field id "${field.id}"`);
    }
    seen.add(field.id);
  }
}

function validateSectionRootShape(schema: SectionSchema): void {
  if (!schema || typeof schema !== "object") {
    throw new SchemaParseError("schema must be an object");
  }
  if (!schema.key || typeof schema.key !== "string") {
    throw new SchemaParseError("schema.key is required and must be a non-empty string");
  }
  if (schema.title !== undefined && typeof schema.title !== "string") {
    throw new SchemaParseError(`[${schema.key}]: schema.title must be a string when provided`);
  }
  if (schema.description !== undefined && typeof schema.description !== "string") {
    throw new SchemaParseError(
      `[${schema.key}]: schema.description must be a string when provided`,
    );
  }
  if (!Array.isArray(schema.fields) || schema.fields.length === 0) {
    throw new SchemaParseError(`[${schema.key}]: schema must declare at least one field`);
  }
}

function validateSectionKind(schema: SectionSchema): void {
  if (schema.scope !== undefined && !VALID_SECTION_SCOPES.has(schema.scope)) {
    throw new SchemaParseError(`[${schema.key}]: invalid schema.scope "${schema.scope}"`);
  }
  if (schema.kind !== undefined && !VALID_SECTION_KINDS.has(schema.kind)) {
    throw new SchemaParseError(`[${schema.key}]: invalid schema.kind "${schema.kind}"`);
  }
  if (schema.kind === "collection" && !schema.instanceDisplay) {
    throw new SchemaParseError(`[${schema.key}]: collection schemas must declare instanceDisplay`);
  }
  if (schema.instanceDisplay && !schema.instanceDisplay.primary) {
    throw new SchemaParseError(`[${schema.key}]: instanceDisplay.primary is required`);
  }
}

/**
 * Validates a SectionSchema is well-formed. Returns the input unchanged on
 * success. Throws SchemaParseError on the first violation.
 */
export function parseSectionSchema(schema: SectionSchema): SectionSchema {
  validateSectionRootShape(schema);
  validateSectionKind(schema);

  const context = `[${schema.key}]`;
  assertUniqueIds(schema.fields, context);
  for (const field of schema.fields) {
    validateField(field, context);
  }
  validateScopeOwnership(schema, context);

  return schema;
}
