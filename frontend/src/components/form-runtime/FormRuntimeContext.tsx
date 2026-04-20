"use client";

import { createContext, useContext } from "react";

import type { AutosaveStatus } from "./AutosaveBanner";
import type { FormRuntimeBridge } from "@/lib/form-runtime/copilot";
import type { SaveMode, SectionSchema } from "@/lib/form-runtime/schema";

export interface FormRuntimeContextValue {
  schema: SectionSchema;
  values: Record<string, unknown>;
  focusedFieldId: string | null;
  /** Runtime default. Per-field schema saveMode overrides this. */
  saveMode: SaveMode;
  /** Autosave state machine — null when saveMode is "explicit". */
  autosaveStatus: AutosaveStatus | null;
  autosaveError: Error | null;
  setFieldValue: (path: string, next: unknown) => void;
  focusField: (id: string | null) => void;
  /** Revert all in-session changes. */
  undoSession: () => void;
  /** Has anything changed since session start? */
  isDirty: boolean;
  /** Stable bridge reference for copilot subscription. */
  bridge: FormRuntimeBridge;
}

export const FormRuntimeContext = createContext<FormRuntimeContextValue | null>(null);

/**
 *
 */
export function useFormRuntime(): FormRuntimeContextValue {
  const ctx = useContext(FormRuntimeContext);
  if (!ctx) {
    throw new Error(
      "useFormRuntime must be used inside <FormRuntimeProvider> (form-runtime section)",
    );
  }
  return ctx;
}
