/**
 * FormRuntimeBridge — the single imperative API copilot uses to read and mutate
 * a mounted form section. Replaces the previous `copilot:field-update` and
 * `copilot:collect-values` window events with a typed, subscribable contract.
 *
 * Contract locked in FLOW-SPEC.md §3.4.
 */

import type { SectionSchema } from "../schema/types";

export interface FocusedFieldState {
  id: string;
  label: string;
  path: string;
}

export interface BridgeSnapshot {
  sectionKey: string;
  schema: SectionSchema;
  values: Record<string, unknown>;
  focusedField: FocusedFieldState | null;
}

export type BridgeListener = (snapshot: BridgeSnapshot) => void;

export interface FormRuntimeBridge {
  /** Returns the active section snapshot, or null if no section is mounted. */
  getSnapshot(): BridgeSnapshot | null;
  /** Patch a field. Delegates to the feature's save function. */
  patchField(fieldPath: string, newValue: unknown): Promise<void>;
  /** Programmatically set focus on a field by id. Pass null to clear. */
  focusField(fieldId: string | null): void;
  /** Subscribe to changes. Returns an unsubscribe function. */
  subscribe(listener: BridgeListener): () => void;
}

export interface BridgeConfig {
  schema: SectionSchema;
  /** Feature provides the live values every time the bridge reads them. */
  getValues: () => Record<string, unknown>;
  /** Feature-provided save function. Receives field path + new value. */
  patchFn: (path: string, value: unknown) => Promise<void>;
}

/**
 * Creates a FormRuntimeBridge instance wired to the feature's schema, live
 * values accessor and save function. One bridge per mounted section.
 */
export function createFormRuntimeBridge(config: BridgeConfig): FormRuntimeBridge {
  const listeners = new Set<BridgeListener>();
  let focused: FocusedFieldState | null = null;

  function snapshot(): BridgeSnapshot {
    return {
      sectionKey: config.schema.key,
      schema: config.schema,
      values: config.getValues(),
      focusedField: focused,
    };
  }

  function notify(): void {
    const snap = snapshot();
    for (const listener of listeners) {
      listener(snap);
    }
  }

  return {
    getSnapshot() {
      return snapshot();
    },
    async patchField(fieldPath, newValue) {
      await config.patchFn(fieldPath, newValue);
      notify();
    },
    focusField(fieldId) {
      if (fieldId === null) {
        focused = null;
      } else {
        const field = config.schema.fields.find((f) => f.id === fieldId);
        focused = field ? { id: field.id, label: field.label, path: field.path } : null;
      }
      notify();
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
  };
}
