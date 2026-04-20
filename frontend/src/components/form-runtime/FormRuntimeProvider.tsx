"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { createFormRuntimeBridge, type FormRuntimeBridge } from "@/lib/form-runtime/copilot";
import { useAutoSave } from "@/lib/form-runtime/hooks";

import { FormRuntimeContext, type FormRuntimeContextValue } from "./FormRuntimeContext";

import type { AutosaveStatus } from "./AutosaveBanner";
import type { SaveMode, SectionSchema } from "@/lib/form-runtime/schema";

const DEFAULT_SAVE_MODE: SaveMode = "autosave-with-banner";

export interface FormRuntimeProviderProps<TValues extends object> {
  schema: SectionSchema;
  initialValues: TValues;
  /** Feature save function. Receives the full composed section object. */
  onSave: (values: TValues) => Promise<void>;
  saveMode?: SaveMode;
  children: ReactNode;
}

/**
 * Owns section state, runs autosave, exposes a stable FormRuntimeBridge via
 * Context. Composes the full values object each time a field changes so
 * consumer save functions (`updateIdentity(fullSectionObject)`) keep working
 * unchanged.
 */
export function FormRuntimeProvider<TValues extends object>({
  schema,
  initialValues,
  onSave,
  saveMode = DEFAULT_SAVE_MODE,
  children,
}: FormRuntimeProviderProps<TValues>) {
  const [values, setValues] = useState<TValues>(initialValues);
  const [focusedFieldId, setFocusedFieldId] = useState<string | null>(null);
  const snapshotRef = useRef<TValues>(initialValues);
  const valuesRef = useRef<TValues>(initialValues);

  useEffect(() => {
    valuesRef.current = values;
  }, [values]);

  const isAutosave = saveMode !== "explicit";

  const autosave = useAutoSave<TValues>({
    saveFn: onSave,
  });

  const setFieldValue = useCallback(
    (path: string, next: unknown) => {
      setValues((prev) => {
        const updated = { ...prev, [path]: next } as TValues;
        if (isAutosave) {
          autosave.trigger(updated);
        }
        return updated;
      });
    },
    [autosave, isAutosave],
  );

  const focusField = useCallback((id: string | null) => {
    setFocusedFieldId(id);
  }, []);

  const undoSession = useCallback(() => {
    setValues(snapshotRef.current);
    if (isAutosave) {
      autosave.trigger(snapshotRef.current);
    }
  }, [autosave, isAutosave]);

  /* eslint-disable react-hooks/refs -- bridge reads valuesRef lazily; invoked only from copilot events, not during render */
  const bridge: FormRuntimeBridge = useMemo(
    () =>
      createFormRuntimeBridge({
        schema,
        getValues: () => valuesRef.current as unknown as Record<string, unknown>,
        patchFn: (path, value) => {
          setFieldValue(path, value);
          return Promise.resolve();
        },
      }),
    [schema, setFieldValue],
  );
  /* eslint-enable react-hooks/refs */

  useEffect(() => {
    bridge.focusField(focusedFieldId);
  }, [bridge, focusedFieldId]);

  // Connect the active bridge to the copilot store so chat UI actions can
  // mutate fields directly (bridge.patchField) instead of dispatching the
  // legacy copilot:field-update window events.
  useEffect(() => {
    const { connectBridge, disconnectBridge } = useCopilotStore.getState();
    connectBridge(bridge);
    return () => {
      disconnectBridge(bridge);
    };
  }, [bridge]);

  // eslint-disable-next-line react-hooks/refs -- snapshotRef is set once at mount and never mutated
  const isDirty = values !== snapshotRef.current;

  const autosaveStatus: AutosaveStatus | null = isAutosave
    ? (autosave.state as AutosaveStatus)
    : null;

  const ctxValue: FormRuntimeContextValue = useMemo(
    () => ({
      schema,
      values: values as unknown as Record<string, unknown>,
      focusedFieldId,
      saveMode,
      autosaveStatus,
      autosaveError: autosave.error,
      setFieldValue,
      focusField,
      undoSession,
      isDirty,
      bridge,
    }),
    [
      schema,
      values,
      focusedFieldId,
      saveMode,
      autosaveStatus,
      autosave.error,
      setFieldValue,
      focusField,
      undoSession,
      isDirty,
      bridge,
    ],
  );

  return <FormRuntimeContext.Provider value={ctxValue}>{children}</FormRuntimeContext.Provider>;
}
