"use client";

import { createElement } from "react";

import { getAction } from "@/lib/form-runtime/actions";

import type { BaseInputProps } from "./types";

/**
 * Renders a custom action component resolved from the action registry.
 * Schema entries of type "custom" provide the action key and optional props.
 * Shows a placeholder when the key is not registered — prevents runtime
 * crashes while Sprint 2 is still porting actions.
 *
 * The registry returns a stable component reference (not a freshly created
 * one), so we use createElement to make that intent obvious to the linter.
 */
export function CustomInput({ field, value, onChange }: BaseInputProps) {
  const actionKey = field.action;
  if (!actionKey) {
    return (
      <div className="rounded border border-destructive/40 bg-destructive/5 p-3 text-xs text-destructive">
        Schema error: custom field &quot;{field.id}&quot; missing action key
      </div>
    );
  }

  const component = getAction(actionKey);
  if (!component) {
    return (
      <div className="rounded border border-dashed border-muted-foreground/40 bg-muted/40 p-3 text-xs text-muted-foreground">
        Acción <code>{actionKey}</code> pendiente de registrar
      </div>
    );
  }

  return createElement(component, { value, onChange, props: field.actionProps });
}
