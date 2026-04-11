// useAutoSave — debounced save helper for section PATCH flows.
// Exposes a narrow state machine: idle → saving → saved | error.
"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type AutoSaveState = "idle" | "saving" | "saved" | "error";

export interface UseAutoSaveOptions<TPayload> {
  /** Function that performs the actual save. Must throw on failure. */
  saveFn: (payload: TPayload) => Promise<void>;
  /** Debounce delay in milliseconds. Defaults to 800. */
  delay?: number;
}

export interface UseAutoSaveResult<TPayload> {
  state: AutoSaveState;
  lastSavedAt: Date | null;
  error: Error | null;
  /** Schedule a save. Subsequent calls within `delay` reset the timer. */
  trigger: (payload: TPayload) => void;
  /** Retry the last failed payload. No-op if there is nothing to retry. */
  retry: () => void;
  /** Cancel any pending save without clearing the last saved timestamp. */
  cancel: () => void;
}

const DEFAULT_DELAY_MS = 800;

export function useAutoSave<TPayload>(
  options: UseAutoSaveOptions<TPayload>,
): UseAutoSaveResult<TPayload> {
  const { saveFn, delay = DEFAULT_DELAY_MS } = options;

  const [state, setState] = useState<AutoSaveState>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingPayloadRef = useRef<TPayload | null>(null);
  // Last payload we attempted to save (set when the debounced timer fires,
  // independent of success/failure). Used by `retry()` to resubmit after errors.
  const lastAttemptedPayloadRef = useRef<TPayload | null>(null);
  const saveFnRef = useRef(saveFn);
  const isMountedRef = useRef(true);

  // Keep the latest saveFn without re-creating callbacks.
  useEffect(() => {
    saveFnRef.current = saveFn;
  }, [saveFn]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []);

  const performSave = useCallback(async (payload: TPayload) => {
    lastAttemptedPayloadRef.current = payload;
    setState("saving");
    setError(null);
    try {
      await saveFnRef.current(payload);
      if (!isMountedRef.current) return;
      setState("saved");
      setLastSavedAt(new Date());
    } catch (err) {
      if (!isMountedRef.current) return;
      const normalised =
        err instanceof Error ? err : new Error("Error al guardar");
      setError(normalised);
      setState("error");
    }
  }, []);

  const trigger = useCallback(
    (payload: TPayload) => {
      pendingPayloadRef.current = payload;
      if (timerRef.current !== null) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        const next = pendingPayloadRef.current;
        pendingPayloadRef.current = null;
        if (next !== null) {
          void performSave(next);
        }
      }, delay);
    },
    [delay, performSave],
  );

  const retry = useCallback(() => {
    const payload =
      pendingPayloadRef.current ?? lastAttemptedPayloadRef.current;
    if (payload === null) return;
    void performSave(payload);
  }, [performSave]);

  const cancel = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    pendingPayloadRef.current = null;
  }, []);

  return {
    state,
    lastSavedAt,
    error,
    trigger,
    retry,
    cancel,
  };
}
