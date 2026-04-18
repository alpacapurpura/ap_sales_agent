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

/**
 * Persistence scope of a section relative to the offer / edition split
 * introduced in Sprint 6 (see DECISIONS.md §D22).
 *
 * - ``offer_level``: every field persists to the top-level entity (e.g.
 *   the ``Offer`` row). All fields render on both the virtual
 *   ``/edition/evergreen/`` URL and specific-edition URLs.
 * - ``edition_level``: every field persists to a nested entity (e.g. a
 *   ``LaunchEdition`` row). Fields hide under the ``evergreen`` URL
 *   because there is no edition to save against.
 * - ``mixed``: fields declare their own ``owner`` (see
 *   :pydata:`FieldOwner`). The runtime dispatcher uses the field's
 *   owner to pick which save callback receives the patch.
 *
 * Unset on legacy consumers (brand-studio) — the runtime treats
 * ``undefined`` as single-owner and calls the section's default save
 * callback for every field.
 */
export type SectionScope = "offer_level" | "edition_level" | "mixed";

/**
 * Which aggregate a single field persists to, within a ``mixed`` section.
 * Ignored on ``offer_level`` / ``edition_level`` sections (the section
 * scope implies the owner uniformly).
 */
export type FieldOwner = "offer" | "edition";

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
  /**
   * Aggregate ownership — required on every field inside a ``mixed``
   * section, forbidden (or must match) on single-owner sections. The
   * runtime routes saves to the owner's configured mutation.
   */
  owner?: FieldOwner;
}

export interface SectionSchema {
  key: string;
  title: string;
  description?: string;
  fields: FieldSchema[];
  /**
   * Persistence scope — set on sections participating in the offer /
   * edition split. Undefined on legacy single-owner sections (the
   * runtime treats them as if the whole section saved to a single
   * callback).
   */
  scope?: SectionScope;
}
