/**
 * Form-runtime schema — declarative description of an editable domain section.
 *
 * A SectionSchema is the single source of truth a feature hands to
 * UniversalEditableSection. The runtime reads it, renders inputs, tracks dirty
 * state, calls the feature's save function, and exposes the section to copilot
 * through FormRuntimeBridge.
 *
 * Contract locked in docs/ux-sessions/2026-04-17-universal-editable-form-component/
 * FLOW-SPEC.md §2.1. Per-field saveMode override added per DECISIONS.md D12.
 */

export type FieldType =
  | "text"
  | "textarea"
  | "enum"
  | "number"
  | "boolean"
  | "url"
  | "email"
  | "array"
  | "custom";

export type SaveMode = "explicit" | "autosave" | "autosave-with-banner";

export interface EnumOption {
  value: string;
  label: string;
}

/**
 * Sub-schema used as array item template. Same shape as SectionSchema minus
 * the top-level key/title (items live inside a parent section).
 */
export interface ItemSchema {
  description?: string;
  fields: FieldSchema[];
}

export interface FieldSchema {
  id: string;
  label: string;
  type: FieldType;
  path: string;
  hint?: string;
  placeholder?: string;
  required?: boolean;
  /** For enum. Must be non-empty when type === "enum". */
  options?: EnumOption[];
  /** For textarea. */
  rows?: number;
  /** For array. Required when type === "array". */
  itemSchema?: ItemSchema;
  /** For custom. Action key registered in the action registry. */
  action?: string;
  /** Props forwarded to the custom action component. Immutable. */
  actionProps?: Record<string, unknown>;
  /** Override runtime default. Use "explicit" for heavy fields (upload, long text). */
  saveMode?: SaveMode;
}

export interface SectionSchema {
  key: string;
  title: string;
  description?: string;
  fields: FieldSchema[];
}
