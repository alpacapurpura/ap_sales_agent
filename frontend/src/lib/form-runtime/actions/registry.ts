/**
 * Action registry — plug-in point for rich custom inputs referenced by
 * FieldSchema entries of type "custom". Features register their action
 * components at module load; the runtime looks them up by key when rendering
 * CustomInput.
 *
 * Contract: ActionComponent receives (value, onChange, props?) and is
 * responsible for its own UI. The runtime does not introspect inside.
 */

import type { ComponentType } from "react";

export interface ActionComponentProps<TValue = unknown, TProps = Record<string, unknown>> {
  value: TValue;
  onChange: (next: TValue) => void;
  props?: TProps;
}

export type ActionComponent<TValue = unknown, TProps = Record<string, unknown>> = ComponentType<
  ActionComponentProps<TValue, TProps>
>;

const registry = new Map<string, ActionComponent>();

export interface RegisterOptions {
  /** Allow replacing an existing entry (used when a placeholder is upgraded). */
  override?: boolean;
}

/**
 * Register a custom action component. Throws if key is empty, component is
 * missing, or key is already registered (unless override: true is set).
 */
export function registerAction(
  key: string,
  component: ActionComponent,
  options: RegisterOptions = {},
): void {
  if (!key || typeof key !== "string") {
    throw new Error("registerAction: key must be a non-empty string");
  }
  if (!component) {
    throw new Error(`registerAction("${key}"): component is required`);
  }
  if (registry.has(key) && !options.override) {
    throw new Error(`registerAction("${key}"): already registered (pass { override: true })`);
  }
  registry.set(key, component);
}

/** Returns the registered component for a key, or undefined. */
export function getAction(key: string): ActionComponent | undefined {
  return registry.get(key);
}

/** Returns true if a component is registered for the key. */
export function hasAction(key: string): boolean {
  return registry.has(key);
}

/** Returns all registered keys sorted alphabetically. Useful for debug UIs and tests. */
export function listActions(): string[] {
  return [...registry.keys()].sort();
}

/** Removes every entry. Intended for test setup only. */
export function clearRegistry(): void {
  registry.clear();
}
