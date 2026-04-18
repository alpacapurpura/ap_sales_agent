/**
 * Runtime validator for SectionSchema. Catches authoring errors at module load
 * so broken schemas never reach the renderer. Throws SchemaParseError with a
 * human-readable message pointing at the offending field id.
 */

import type { FieldSchema, FieldType, ItemSchema, SaveMode, SectionSchema } from "./types";

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

/**
 * Validates a SectionSchema is well-formed. Returns the input unchanged on
 * success. Throws SchemaParseError on the first violation.
 */
export function parseSectionSchema(schema: SectionSchema): SectionSchema {
  if (!schema || typeof schema !== "object") {
    throw new SchemaParseError("schema must be an object");
  }
  if (!schema.key || typeof schema.key !== "string") {
    throw new SchemaParseError("schema.key is required and must be a non-empty string");
  }
  if (!schema.title || typeof schema.title !== "string") {
    throw new SchemaParseError(`[${schema.key}]: schema.title is required`);
  }
  if (!Array.isArray(schema.fields) || schema.fields.length === 0) {
    throw new SchemaParseError(`[${schema.key}]: schema must declare at least one field`);
  }

  const context = `[${schema.key}]`;
  assertUniqueIds(schema.fields, context);
  for (const field of schema.fields) {
    validateField(field, context);
  }

  return schema;
}
