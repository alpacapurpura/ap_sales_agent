"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";

import { useNavigation } from "@/components/shared/navigation";

import { useCopilotStore, type UIAction } from "../store/copilot-store";

export type { UIAction };

/**
 * Wait for a DOM element to appear by polling every 100ms.
 * Resolves with the element when found, or null if maxMs elapses.
 * Returns a cleanup function to cancel the poll early (e.g. on unmount).
 */
function waitForElement(
  selector: string,
  maxMs = 3000,
): { promise: Promise<Element | null>; cancel: () => void } {
  let cancelled = false;
  let intervalId: ReturnType<typeof setInterval> | null = null;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const promise = new Promise<Element | null>((resolve) => {
    intervalId = setInterval(() => {
      if (cancelled) {
        resolve(null);
        return;
      }
      const el = document.querySelector(selector);
      if (el) {
        if (intervalId !== null) clearInterval(intervalId);
        if (timeoutId !== null) clearTimeout(timeoutId);
        resolve(el);
      }
    }, 100);

    timeoutId = setTimeout(() => {
      if (intervalId !== null) clearInterval(intervalId);
      resolve(null);
    }, maxMs);
  });

  const cancel = () => {
    cancelled = true;
    if (intervalId !== null) clearInterval(intervalId);
    if (timeoutId !== null) clearTimeout(timeoutId);
  };

  return { promise, cancel };
}

/**
 * Add the copilot-highlight class to an element and schedule its removal.
 * Returns a cleanup function that removes the highlight immediately.
 */
function highlightElement(el: Element): () => void {
  el.classList.add("copilot-highlight");
  const removeId = setTimeout(() => {
    if (document.contains(el)) {
      el.classList.remove("copilot-highlight");
    }
  }, 3000);

  return () => {
    clearTimeout(removeId);
    if (document.contains(el)) {
      el.classList.remove("copilot-highlight");
    }
  };
}

/**
 * Build a CSS selector for a section or field ID.
 * Tries `#id` first (getElementById equivalent) then falls back to data-* attrs.
 */
function buildSectionSelector(sectionId: string): string {
  return `#${CSS.escape(sectionId)}, [data-section="${sectionId}"]`;
}

function buildFieldSelector(fieldId: string): string {
  const escaped = CSS.escape(fieldId);
  return (
    `#${escaped}, ` +
    `[data-field-id="${fieldId}"], ` +
    `[data-field-anchor="${fieldId}"], ` +
    `[name="${fieldId}"]`
  );
}

/**
 * Executes UI actions received from the copilot backend via SSE.
 * Also processes the pending action queue from the store.
 */
export function useCopilotNavigator() {
  const { navigate } = useNavigation();
  const params = useParams();
  const tenantId = params?.tenantId as string | undefined;
  const pendingUIActions = useCopilotStore((s) => s.pendingUIActions);

  // Track all in-flight poll cancellers so we can clean up on unmount.
  const cancelersRef = useRef<(() => void)[]>([]);

  // Cancel all in-flight polls and highlights when the hook unmounts.
  useEffect(() => {
    return () => {
      for (const cancel of cancelersRef.current) {
        cancel();
      }
      cancelersRef.current = [];
    };
  }, []);

  const executeAction = useCallback(
    (action: UIAction) => {
      switch (action.type) {
        case "navigate": {
          if (!action.route) break;
          // Replace {tenantId} placeholder with actual tenant.
          const route = tenantId ? action.route.replace(/{tenantId}/g, tenantId) : action.route;
          navigate(route);

          // If a section_id is provided, wait for it to appear in the DOM
          // instead of using a fixed timer.
          if (action.section_id) {
            const selector = buildSectionSelector(action.section_id);
            const { promise, cancel } = waitForElement(selector);

            cancelersRef.current.push(cancel);

            void promise.then((el) => {
              // Remove this canceller from the active list.
              cancelersRef.current = cancelersRef.current.filter((c) => c !== cancel);

              if (!el) return; // Element never appeared — give up silently.

              el.scrollIntoView({ behavior: "smooth", block: "center" });
              const removeHighlight = highlightElement(el);
              cancelersRef.current.push(removeHighlight);
            });
          }
          break;
        }

        case "scroll_to_field": {
          if (!action.field_id) break;
          const selector = buildFieldSelector(action.field_id);
          const el = document.querySelector(selector);
          if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "center" });
            const removeHighlight = highlightElement(el);
            cancelersRef.current.push(removeHighlight);
          }
          break;
        }

        case "open_form": {
          window.dispatchEvent(
            new CustomEvent("copilot:open-form", {
              detail: {
                formId: action.form_id,
                prefillData: action.prefill_data,
              },
            }),
          );
          break;
        }
      }
    },
    [navigate, tenantId],
  );

  // Process pending actions — read queue from store directly to avoid
  // unstable array reference in deps causing effect churn.
  const pendingLength = pendingUIActions.length;
  useEffect(() => {
    if (pendingLength === 0) return;
    const action = useCopilotStore.getState().dequeuUIAction();
    if (action) {
      executeAction(action);
    }
  }, [pendingLength, executeAction]);

  return { executeAction };
}
